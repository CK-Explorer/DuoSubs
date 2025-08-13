"""
Manages shared SentenceTransformer model instances for web UI sessions.

This module provides the ModelPool class, which loads, tracks, and releases models
across multiple sessions, ensuring efficient memory usage and safe concurrent access.
"""
import gc
import threading
import time
import weakref
from typing import Any, Callable, ClassVar

import gradio as gr
import torch
from sentence_transformers import SentenceTransformer


class ModelPool:
    """
    A pool to manage shared SentenceTransformer model instances across sessions.

    Models are keyed by (model_name, device_type) and reference counted by session IDs.
    When no session uses a model, it is released from memory.
    """
    _lock = threading.Lock()
    _models: ClassVar[
        dict[tuple[str, str], tuple[SentenceTransformer, set[str]]] 
    ] = {}  # (model_name, device_type) -> (model_instance, set_of_session_ids)

    @classmethod
    def load_model(
        cls,
        session_id: str | None,
        model_name: str,
        device: str,
        loaded_fn: Callable[[], SentenceTransformer]
    ) -> SentenceTransformer:
        """
        Loads or retrieves a shared SentenceTransformer model for a session.

        This method ensures that the model is loaded only once per (model_name, device)
        combination and is shared across sessions. If the model is already loaded, it 
        returns the existing instance.

        Args:
            session_id (str | None): Unique identifier for the session.
            model_name (str): Name of the model to load.
            device (str): Device type (e.g., 'cpu', 'cuda', 'cuda:0').
            loaded_fn (Callable[[], SentenceTransformer]): Callable that loads and 
                returns a SentenceTransformer instance.

        Returns:
            SentenceTransformer: The loaded or shared model instance.

        Raises:
            ValueError: If session_id is None.
        """
        if session_id is None:
            raise ValueError("Expected non-None session id.")
        
        key = (model_name, device)
        with cls._lock:
            if key not in cls._models:
                model = loaded_fn()
                cls._models[key] = (model, set())
            model, users = cls._models[key]
            users.add(session_id)
            return model

    @classmethod
    def unload_model(cls, session_id: str | None) -> None:
        """
        Removes a session's reference to models and releases unused models from memory.

        This method checks if the session_id is associated with any models and removes 
        it. If no sessions are using a model, it releases the model from memory.

        Args:
            session_id (str | None): Unique identifier for the session.

        Raises:
            ValueError: If session_id is None.
        """
        if session_id is None:
            raise ValueError("Expected non-None session id.")

        with cls._lock:
            keys_to_delete = []
            weak_ref = None
            for key, (model, users) in cls._models.items():
                if session_id in users:
                    users.remove(session_id)
                    if not users:
                        keys_to_delete.append(key)
                        weak_ref = weakref.ref(model)

            for key in keys_to_delete:
                del cls._models[key]
                if weak_ref is not None:
                    ModelPool._wait_for_release(weak_ref, 10)

    @staticmethod
    def _wait_for_release(
        weak_ref: weakref.ReferenceType[Any],
        timeout: float = 5.0,
        interval: float = 0.5
    ) -> None:
        """
        Waits for a model to be released from memory, with periodic garbage collection.

        Args:
            weak_ref (weakref.ReferenceType[Any]): Weak reference to the model object.
            timeout (float): Maximum time to wait (seconds).
            interval (float): Time between checks (seconds).
        """
        start = time.time()
        model_released = False
        while time.time() - start < timeout:
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect() # type: ignore[no-untyped-call]
            if ModelPool._is_model_released(weak_ref):
                model_released = True
                break
            time.sleep(interval)
        
        if not model_released:
            gr.Warning(
                "The model could not be unloaded. "
                "If you're out of RAM or VRAM, try restarting the script "
                "— simply reloading the webpage will not help."
            )

    @staticmethod
    def _is_model_released(weak_ref: weakref.ReferenceType[Any]) -> bool:
        """
        Checks if the model object has been released from memory.

        Args:
            weak_ref (weakref.ReferenceType[Any]): Weak reference to the model object.

        Returns:
            bool: True if the model is released, False otherwise.
        """
        gc.collect()
        alive = weak_ref() is not None
        return not alive
