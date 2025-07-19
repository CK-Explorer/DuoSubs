"""
Unit tests for the merge pipeline in duosubs.core.merge_pipeline.

This module contains pytest-based unit tests for loading subtitles, model loading, 
merging, saving, and utility functions in the merge pipeline. It uses monkeypatching to 
simulate dependencies and error conditions.
"""
from pathlib import Path
from typing import Any, NoReturn, TypedDict, cast
from unittest.mock import MagicMock, Mock
from zipfile import ZipFile

import pysubs2
import pytest

from duosubs.common.enums import DeviceType, OmitFile, SubtitleFormat
from duosubs.common.exceptions import (
    LoadModelError,
    LoadSubsError,
    MergeSubsError,
    SaveSubsError,
)
from duosubs.common.types import MergeArgs
from duosubs.core.merge_pipeline import (
    _retain_files,
    _save_file,
    load_sentence_transformer_model,
    load_subtitles,
    merge_subtitles,
    save_subtitles_in_zip,
)
from duosubs.subtitle.data import SubtitleData
from duosubs.subtitle.field import SubtitleField
from tests.common_utils.utils import load_test_cases

# Test cases paths
DATA_PATH: Path = Path(__file__).parent / "data"
DATA_RETAIN_FILES: Path = DATA_PATH / "retain_files.yaml"

# ----------------------------
# TypedDict Definitions for Tests
# ----------------------------

class RetainFilesTests(TypedDict):
    """
    Represents a test case for the _retain_files utility function.

    Attributes:
        input (list[str]): List of OmitFile enum values as strings.
        expected (list[bool]): Expected output list indicating which files to retain.
    """
    input: list[str]
    expected: list[bool]

# ----------------------------
# Load Subtitles Tests
# ----------------------------

def test_load_subtitles_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Test the load_subtitles function for successful loading of primary and secondary 
    subtitles.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture for monkeypatching functions.
    """
    args = MergeArgs(primary="tests/en.srt", secondary="tests/zh.srt")
    subs = [SubtitleField(start=1000, end=2000, primary_text="p1")]
    styles = pysubs2.SSAFile()
    styles.rename_style("Default", "Primary_style")
    tokens = ["toks"]
    styles_tokens = ["style_toks"]

    sub_data = SubtitleData(
        subs=subs,
        styles=styles,
        tokens=tokens,
        styles_tokens=styles_tokens
    )

    monkeypatch.setattr(
        "duosubs.core.merge_pipeline.load_subs", lambda p: sub_data
    )

    primary_subs_data, secondary_subs_data = load_subtitles(args)

    assert primary_subs_data == secondary_subs_data
    assert primary_subs_data.subs == subs
    assert primary_subs_data.styles == styles
    assert primary_subs_data.tokens == tokens
    assert primary_subs_data.styles_tokens == styles_tokens

def test_load_subtitles_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Test load_subtitles function for error handling when loading subtitles fails for 
    either primary or secondary.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture for monkeypatching functions.
        primary_error (bool): Whether to simulate error in primary or secondary loading.
    """
    args = MergeArgs(primary="tests/en.srt", secondary="tests/zh.srt")

    monkeypatch.setattr("duosubs.core.merge_pipeline.load_subs", raise_error)

    with pytest.raises(LoadSubsError):
        load_subtitles(args)

def test_load_empty_subtitle(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Test load_subtitles function for error handling when either subtitle file is empty.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture for monkeypatching functions.
    """
    args = MergeArgs(primary="tests/en.srt", secondary="tests/zh.srt")
    styles = pysubs2.SSAFile()
    styles.rename_style("Default", "Primary_style")

    sub_data = SubtitleData(
        subs=[],
        styles=styles,
        tokens=["toks"],
        styles_tokens=["style_toks"]
    )

    monkeypatch.setattr(
        "duosubs.core.merge_pipeline.load_subs", lambda p: sub_data
    )

    with pytest.raises(LoadSubsError):
        load_subtitles(args)

# ----------------------------
# Load Model Tests
# ----------------------------

def test_load_model_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Test load_sentence_transformer_model function for successful loading of a sentence 
    transformer model.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture for monkeypatching functions.
    """
    fake_model = Mock(name="FakeModel")

    monkeypatch.setattr(
        "duosubs.core.merge_pipeline._auto_select_device", lambda: "cpu"
    )
    monkeypatch.setattr(
        "duosubs.core.merge_pipeline.SentenceTransformer", lambda *a, **kw: fake_model
    )

    args = MergeArgs(model="LaBSE", device=DeviceType.AUTO)

    result = load_sentence_transformer_model(args)
    assert result == fake_model

def test_load_model_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Test load_sentence_transformer_model function for error handling when model loading 
    fails.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture for monkeypatching functions.
    """
    monkeypatch.setattr(
        "duosubs.core.merge_pipeline._auto_select_device", lambda: "cpu"
    )
    monkeypatch.setattr("duosubs.core.merge_pipeline.SentenceTransformer", raise_error)

    args = MergeArgs(model="bad-model", device=DeviceType.AUTO)

    with pytest.raises(LoadModelError):
        load_sentence_transformer_model(args)

# ----------------------------
# Merge Subtitles Tests
# ----------------------------

@pytest.mark.parametrize("success", [True, False])
def test_merge_subtitles(monkeypatch: pytest.MonkeyPatch, success: bool) -> None:
    """
    Test merge_subtitle function, both successful and error cases.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture for monkeypatching functions.
        success (bool): Whether to simulate a successful or failing merge.
    """
    fake_model = MagicMock()

    primary_styles = pysubs2.SSAFile()
    primary_styles.rename_style("Default", "ENGLISH")
    primary_subs_data = SubtitleData(
        subs=[SubtitleField(start=0, end=1000, primary_text="Hi")],
        styles=primary_styles,
        tokens=["Hi"],
        styles_tokens=["ENGLISH"]
    )

    secondary_styles = pysubs2.SSAFile()
    secondary_styles.rename_style("Default", "ENGLISH")
    secondary_subs_data = SubtitleData(
        subs=[SubtitleField(start=0, end=1000, secondary_text="Bonjour")],
        styles=secondary_styles,
        tokens=["Bonjour"],
        styles_tokens=["FRENCH"]
    )

    args = MergeArgs(primary="a.srt", secondary="b.srt", model="LaBSE")
    merged_subs = [
        SubtitleField(
            start=0,
            end=1000,
            primary_text="Hi",
            secondary_text="Bonjour"
    )]

    if success:
        class FakeMerger:
            def __init__(self, *_a: Any, **_kw: Any) -> None:
                pass

            def merge_subtitle(self, *_a: Any, **_kw: Any) -> list[SubtitleField]:
                return merged_subs

        monkeypatch.setattr("duosubs.core.merge_pipeline.Merger", FakeMerger)
        result = merge_subtitles(
            args,
            fake_model,
            primary_subs_data,
            secondary_subs_data,
            [False]
        )
        assert isinstance(result, list)
        assert result == merged_subs
    else:
        class FailingMerger:
            def __init__(self, *_a: Any, **_kw: Any) -> None:
                pass

            def merge_subtitle(self, *_a: Any, **_kw: Any) -> NoReturn:
                raise_error()

        monkeypatch.setattr("duosubs.core.merge_pipeline.Merger", FailingMerger)
        with pytest.raises(MergeSubsError):
            merge_subtitles(
                args,
                fake_model,
                primary_subs_data,
                secondary_subs_data,
                [False]
            )

# ----------------------------
# Save Subtitle Tests
# ----------------------------

@pytest.mark.parametrize("success", [True, False])
def test_save_subtitles_in_zip(monkeypatch: pytest.MonkeyPatch, success: bool) -> None:
    """
    Test save_subtitles_in_zip function, both successful and error cases.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest fixture for monkeypatching functions.
        success (bool): Whether to simulate a successful or failing save.
    """
    subs = [SubtitleField(start=0, end=1000, primary_text="Test")]
    primary_styles = MagicMock()
    secondary_styles = MagicMock()

    args = MergeArgs(
        primary="a.srt",
        secondary="b.srt",
        model="LaBSE",
        format_all=SubtitleFormat.ASS
    )

    monkeypatch.setattr(
        "duosubs.core.merge_pipeline._retain_files", 
        lambda omit: ["combined", "primary", "secondary"]
    )
    monkeypatch.setattr(Path, "mkdir", lambda *a, **kw: None)

    if success:
        monkeypatch.setattr(
            "duosubs.core.merge_pipeline._save_file",
            lambda *a, **kw: None
        )
        save_subtitles_in_zip(args, subs, primary_styles, secondary_styles)
    else:
        monkeypatch.setattr("duosubs.core.merge_pipeline._save_file", raise_error)
        with pytest.raises(SaveSubsError):
            save_subtitles_in_zip(args, subs, primary_styles, secondary_styles)

# ----------------------------
# Utility Functions Tests
# ----------------------------

def test_save_file_outputs_zip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Test that _save_file writes all expected files to the output zip archive.

    Args:
        tmp_path (Path): Temporary directory provided by pytest.
        monkeypatch (pytest.MonkeyPatch): Pytest fixture for monkeypatching functions.
    """
    output_name = "test_output"
    output_dir = tmp_path
    retained = [True, True, True, True]
    formats = ["srt", "ass", "vtt"]

    monkeypatch.setattr(
        "duosubs.core.merge_pipeline.save_memory_combined",
        lambda *a, **kw: "COMBINED_CONTENT"
    )
    monkeypatch.setattr(
        "duosubs.core.merge_pipeline.save_memory_separate",
        lambda *a, **kw: ("PRIMARY_CONTENT", "SECONDARY_CONTENT")
    )
    monkeypatch.setattr(
        "duosubs.core.merge_pipeline.save_memory_edit",
        lambda *a, **kw: b"EDIT_BYTES"
    )

    _save_file(
        subs=[SubtitleField(start=0, end=1000, primary_text="Test")],
        primary_styles=MagicMock(),
        secondary_styles=MagicMock(),
        output_name=output_name,
        output_dir=output_dir,
        retained_file_tuple=retained,
        subs_fmt=formats,
        secondary_above=False,
        retain_newline=False
    )

    zip_path = output_dir / f"{output_name}.zip"
    assert zip_path.exists()

    with ZipFile(zip_path, "r") as zipf:
        assert f"{output_name}_combined.srt" in zipf.namelist()
        assert f"{output_name}_primary.ass" in zipf.namelist()
        assert f"{output_name}_secondary.vtt" in zipf.namelist()
        assert f"{output_name}.json.gz" in zipf.namelist()

        assert zipf.read(f"{output_name}_combined.srt").decode() == "COMBINED_CONTENT"
        assert zipf.read(f"{output_name}_primary.ass").decode() == "PRIMARY_CONTENT"
        assert zipf.read(f"{output_name}_secondary.vtt").decode() == "SECONDARY_CONTENT"
        assert zipf.read(f"{output_name}.json.gz").decode() == "EDIT_BYTES"

@pytest.mark.parametrize(
    "case", 
    cast(list[RetainFilesTests], load_test_cases(DATA_RETAIN_FILES))
)
def test_retain_files(case: RetainFilesTests) -> None:
    """
    Test the _retain_files utility for correct file retention logic.

    Args:
        case (RetainFilesTests): Test case data loaded from YAML.
    """
    inputs = case["input"]
    omit_list= [OmitFile[d] for d in inputs]
    assert _retain_files(omit_list)==case["expected"]

# ----------------------------
# Helper functions
# ----------------------------

def raise_error(*_args: Any, **_kwargs: Any) -> NoReturn:
    """
    Helper function to raise a RuntimeError for simulating errors in monkeypatching.
    """
    raise RuntimeError("Error.")
