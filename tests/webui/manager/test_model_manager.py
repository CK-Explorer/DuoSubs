
"""
Unit tests for the ModelPool class in DuoSubs web UI, covering model loading, reuse, 
unloading, and memory release logic.
"""

import weakref
from unittest.mock import MagicMock, patch

from sentence_transformers import SentenceTransformer

from duosubs.webui.manager.model_manager import ModelPool


def test_load_model_first_time() -> None:
    """
    Test loading a model for the first time adds it to the pool and calls the loader.
    """
    session_id = "user1234"
    model_name = "test-model"
    device = "cpu"

    dummy_model = MagicMock(spec=SentenceTransformer)
    loader_fn = MagicMock(return_value=dummy_model)

    ModelPool._models.clear()
    model = ModelPool.load_model(session_id, model_name, device, loader_fn)

    assert model is dummy_model
    key = (model_name, device)
    assert key in ModelPool._models
    stored_model, sessions = ModelPool._models[key]
    assert stored_model is dummy_model
    assert session_id in sessions
    loader_fn.assert_called_once()

def test_load_model_reuse() -> None:
    """
    Test loading a model for a second session reuses the same model instance.
    """
    session_id1 = "user1234"
    session_id2 = "user2456"
    model_name = "test-model"
    device = "cpu"

    dummy_model = MagicMock(spec=SentenceTransformer)
    loader_fn = MagicMock(return_value=dummy_model)

    ModelPool._models.clear()
    ModelPool.load_model(session_id1, model_name, device, loader_fn)
    model = ModelPool.load_model(session_id2, model_name, device, loader_fn)

    assert model is dummy_model
    key = (model_name, device)
    _, sessions = ModelPool._models[key]
    assert session_id1 in sessions
    assert session_id2 in sessions

    loader_fn.assert_called_once()

def test_unload_model_removes_session_and_model() -> None:
    """
    Test unloading the last session removes the model from the pool and calls 
    _wait_for_release.
    """
    session_id = "user1234"
    model_name = "test-model"
    device = "cuda"
    key = (model_name, device)

    dummy_model = MagicMock(spec=SentenceTransformer)

    ModelPool._models.clear()
    ModelPool._models[key] = (dummy_model, {session_id})

    with patch.object(ModelPool, "_wait_for_release") as mock_wait:
        ModelPool.unload_model(session_id)

        assert key not in ModelPool._models
        mock_wait.assert_called_once()
        called_ref = mock_wait.call_args.args[0]
        assert called_ref() is dummy_model

def test_unload_model_only_removes_session() -> None:
    """
    Test unloading one of multiple sessions only removes that session, not the model.
    """
    session_id1 = "user1234"
    session_id2 = "user2468"
    model_name = "test-model"
    device = "cpu"
    key = (model_name, device)

    dummy_model = MagicMock(spec=SentenceTransformer)
    ModelPool._models.clear()
    ModelPool._models[key] = (dummy_model, {session_id1, session_id2})

    with patch.object(ModelPool, "_wait_for_release") as mock_wait:
        ModelPool.unload_model(session_id1)

        assert key in ModelPool._models
        _, sessions = ModelPool._models[key]
        assert session_id1 not in sessions
        assert session_id2 in sessions
        mock_wait.assert_not_called()

def test_wait_for_release_success() -> None:
    """
    Test that _wait_for_release returns early if the model is released before timeout.
    """
    class DummyModel:
        pass

    model = DummyModel()
    weak_ref = weakref.ref(model)

    release_check_results = [False, True]

    with patch("gc.collect"), \
        patch("torch.cuda.is_available", return_value=True), \
        patch("torch.cuda.empty_cache"), \
        patch("torch.cuda.ipc_collect"), \
        patch(
            "duosubs.webui.manager.model_manager.ModelPool._is_model_released",
            side_effect=lambda ref: release_check_results.pop(0)
        ), \
        patch("time.sleep", return_value=None), \
        patch("time.time") as mock_time:
        
        mock_time.side_effect = [0, 0.1, 0.2]  # each iteration
        ModelPool._wait_for_release(weak_ref, timeout=1, interval=0.1)

def test_wait_for_release_timeout() -> None:
    """
    Test that _wait_for_release triggers a warning if the model is not released in time.
    """
    class DummyModel:
        pass

    model = DummyModel()
    weak_ref = weakref.ref(model)

    with patch("gc.collect"), \
        patch("torch.cuda.is_available", return_value=True), \
        patch("torch.cuda.empty_cache"), \
        patch("torch.cuda.ipc_collect"), \
        patch(
            "duosubs.webui.manager.model_manager.ModelPool._is_model_released",
            return_value=False
        ), \
        patch("time.sleep", return_value=None), \
        patch("time.time", side_effect=[0, 1, 2, 3, 4, 5, 6]), \
        patch("duosubs.webui.manager.model_manager.gr.Warning") as mock_warning:

        ModelPool._wait_for_release(weak_ref, timeout=5, interval=1)

        mock_warning.assert_called_once()
