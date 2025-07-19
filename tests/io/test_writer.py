"""
Unit tests for subtitle writer functions in duosubs.io.writer.

This module contains pytest-based unit tests for round-trip saving and loading of 
subtitle files in various formats, including edit, combined, and separate subtitle 
streams. It also includes helper functions for correctness checks.
"""

import gzip
import io
import json
from math import floor
from pathlib import Path

import pysubs2
import pytest

from duosubs.common.constants import SUPPORTED_NATIVE_SUB_EXT, SUPPORTED_SUB_EXT
from duosubs.io.loader import load_file_edit
from duosubs.io.utils import _decode, _deserialize_styles
from duosubs.io.writer import (
    save_file_combined,
    save_file_edit,
    save_file_separate,
    save_memory_combined,
    save_memory_edit,
    save_memory_separate,
)
from duosubs.subtitle.field import SubtitleField

# Test subtitle paths
SUB_PATH: Path = Path(__file__).parent / "sub_data"
SUB_COMPRESSED_DATA: Path = SUB_PATH / "TOS-en-cht.json.gz"
COMBINED_PRIMARY_ABOVE: Path = SUB_PATH / "combined/primary_above/TOS-en-cht"
COMBINED_SECONDARY_ABOVE: Path = SUB_PATH / "combined/secondary_above/TOS-en-cht"

# ----------------------------
# File Edit Round Trip Tests
# ----------------------------

def test_file_edit_round_trip(tmp_path: Path) -> None:
    """
    Test save_file_edit and load_file_edit functions for round-trip saving and loading
    of compressed edit subtitle files.

    Args:
        tmp_path (Path): Temporary directory provided by pytest for file output.
    """
    subs_m, styles_p, styles_s = load_file_edit(str(SUB_COMPRESSED_DATA))
    output = tmp_path / 'test.json'
    save_file_edit(subs_m, styles_p, styles_s, str(output))
    output = tmp_path / 'test.json.gz'
    assert output.exists()

    (
        new_subs_m,
        new_styles_p,
        new_styles_s
    ) = load_file_edit(str(output))

    assert subs_m == new_subs_m
    assert styles_p.styles == new_styles_p.styles
    assert styles_s.styles == new_styles_s.styles

def test_memory_edit_round_trip() -> None:
    """
    Test load_file_edit and save_memory_edit functions for round-trip saving and loading
    of compressed edit subtitle files in memory.
    """
    subs_m, styles_p, styles_s = load_file_edit(str(SUB_COMPRESSED_DATA))
    compressed_data = save_memory_edit(subs_m, styles_p, styles_s)

    decompressed_buffer = io.BytesIO(compressed_data)
    with gzip.GzipFile(fileobj=decompressed_buffer, mode="r") as gz:
        decompressed_bytes = gz.read()
        data = _decode(
            json.loads(decompressed_bytes.decode("utf-8"))
        )

    new_styles_p = _deserialize_styles(data['primary_styles'])
    new_styles_s = _deserialize_styles(data['secondary_styles'])
    new_subs_m = [SubtitleField(**s) for s in data['subtitles']]

    assert subs_m == new_subs_m
    assert styles_p.styles == new_styles_p
    assert styles_s.styles == new_styles_s

# ----------------------------
# Combined Subtitle Round Trip Tests
# ----------------------------

@pytest.mark.parametrize("desc, secondary_above, retain_newline, path_prefix", [
    ("primary_newline", False, True, COMBINED_PRIMARY_ABOVE),
    ("primary_no_newline", False, False, COMBINED_PRIMARY_ABOVE),
    ("secondary_newline", True, True, COMBINED_SECONDARY_ABOVE),
    ("secondary_no_newline", True, False, COMBINED_SECONDARY_ABOVE),
])
@pytest.mark.parametrize("is_memory", [True, False])
@pytest.mark.parametrize("ext", SUPPORTED_SUB_EXT)
def test_combined_round_trip(
        tmp_path: Path,
        ext: str,
        is_memory: bool,
        desc: str,
        secondary_above: bool,
        retain_newline: bool,
        path_prefix: str
    ) -> None:
    """
    Test save_memory_combined and save_file_combined functions for round-trip saving and
    loading of combined bilingual subtitle files.

    Args:
        tmp_path (Path): Temporary directory provided by pytest for file output.
        ext (str): Subtitle file extension/format.
        is_memory (bool): Whether to test in-memory or file-based saving.
        desc (str): Description of the test case.
        secondary_above (bool): If True, secondary text is above primary.
        retain_newline (bool): Whether to retain line breaks.
        path_prefix (str): Path prefix for test files.
    """
    suffix = "_".join(desc.split("_")[1:])
    test_path = Path(f"{path_prefix}_{suffix}.{ext}")
    subs_m, styles_p, styles_s = load_file_edit(str(SUB_COMPRESSED_DATA))
    if is_memory:
        subs_str = save_memory_combined(
            subs_m,
            styles_p, styles_s,
            ext,
            secondary_above,
            retain_newline
        )
        subs_save = pysubs2.SSAFile.from_string(subs_str.decode("utf-8"), format_=ext)
    else:
        output = tmp_path / str('test.' + ext)
        save_file_combined(
            subs_m,
            styles_p, styles_s,
            output,
            secondary_above,
            retain_newline
        )
        assert output.exists()
        subs_save = pysubs2.load(str(output), format_=ext)

    subs_ori = pysubs2.load(str(test_path), format_=ext)
    assert_combined_correctness(subs_ori, subs_save, ext)

# ----------------------------
# Separate Subtitle Round Trip Tests
# ----------------------------

@pytest.mark.parametrize("retain_newline", [True, False])
@pytest.mark.parametrize("is_memory", [True, False])
@pytest.mark.parametrize("ext", SUPPORTED_SUB_EXT)
def test_separate_round_trip(
    tmp_path: Path,
    ext: str,
    is_memory: bool,
    retain_newline: bool
    ) -> None:
    """
    Test save_memory_separate and save_file_separate functions for round-trip saving and
    loading of separate primary and secondary subtitle files.

    Args:
        tmp_path (Path): Temporary directory provided by pytest for file output.
        ext (str): Subtitle file extension/format.
        is_memory (bool): Whether to test in-memory or file-based saving.
        retain_newline (bool): Whether to retain line breaks.
    """
    subs_m, styles_p, styles_s = load_file_edit(str(SUB_COMPRESSED_DATA))
    if is_memory:
        subs_p_str, subs_s_str = save_memory_separate(
            subs_m,
            styles_p, styles_s,
            ext, ext,
            retain_newline
        )
        subs_p = pysubs2.SSAFile.from_string(subs_p_str.decode("utf-8"), format_=ext)
        subs_s = pysubs2.SSAFile.from_string(subs_s_str.decode("utf-8"), format_=ext)
    else:
        output_p = tmp_path / str('primary.' + ext)
        output_s = tmp_path / str('secondary.' + ext)
        save_file_separate(
            subs_m,
            styles_p, styles_s,
            output_p, output_s,
            retain_newline
        )
        assert output_p.exists()
        assert output_s.exists()
        subs_p = pysubs2.load(str(output_p), format_=ext)
        subs_s = pysubs2.load(str(output_s), format_=ext)

    assert_separate_correctness(
        subs_m, subs_p, subs_s,
        styles_p, styles_s,
        ext,
        retain_newline
    )

# ----------------------------
# Helper functions
# ----------------------------

def assert_combined_correctness(
        subs_ori: pysubs2.SSAFile,
        subs_save: pysubs2.SSAFile,
        ext: str
    ) -> None:
    """
    Helper to assert correctness of combined subtitle files after round-trip.

    Args:
        subs_ori (pysubs2.SSAFile): Original subtitle file.
        subs_save (pysubs2.SSAFile): Saved and reloaded subtitle file.
        ext (str): Subtitle file extension/format.
    """
    assert len(subs_save) == len(subs_ori)

    if ext in SUPPORTED_NATIVE_SUB_EXT:
        assert subs_save.styles == subs_ori.styles

    for sub_s, sub_o in zip(subs_save, subs_ori, strict=False):
        if ext == 'tmp':
            assert to_tmp_time(sub_s.start) == to_tmp_time(sub_o.start)
        else:
            assert sub_s.start == sub_o.start
            assert sub_s.end == sub_o.end

        assert sub_s.text == sub_o.text

def assert_separate_correctness(
        subs_m: list[SubtitleField],
        subs_p: pysubs2.SSAFile,
        subs_s: pysubs2.SSAFile,
        styles_p: pysubs2.SSAFile,
        styles_s: pysubs2.SSAFile,
        ext: str, retain_newline: bool
    ) -> None:
    """
    Helper to assert correctness of separate subtitle files after round-trip.

    Args:
        subs_m (list[SubtitleField]): List of merged subtitle fields.
        subs_p (pysubs2.SSAFile): Primary subtitle file.
        subs_s (pysubs2.SSAFile): Secondary subtitle file.
        styles_p (pysubs2.SSAFile): Primary styles.
        styles_s (pysubs2.SSAFile): Secondary styles.
        ext (str): Subtitle file extension/format.
        retain_newline (bool): Whether to retain line breaks.
    """
    assert len(subs_p) == len(subs_m)
    assert len(subs_s) == len(subs_m)

    if ext in SUPPORTED_NATIVE_SUB_EXT:
        assert subs_p.styles == styles_p.styles
        assert subs_s.styles == styles_s.styles

    for sub_p, sub_s, sub_ori in zip(subs_p, subs_s, subs_m, strict=False):
        if ext == 'tmp':
            assert to_tmp_time(sub_p.start) == to_tmp_time(sub_ori.start)
            assert to_tmp_time(sub_s.start) == to_tmp_time(sub_ori.start)
        else:
            assert sub_p.start == sub_ori.start
            assert sub_s.start == sub_ori.start
            assert sub_p.end == sub_ori.end
            assert sub_s.end == sub_ori.end

        if retain_newline:
            expected_p = sub_ori.primary_text.strip()
            expected_s = sub_ori.secondary_text.strip()
        else:
            expected_p = sub_ori.primary_text.replace('\\N', ' ').strip()
            expected_s = sub_ori.secondary_text.replace('\\N', ' ').strip()

        assert sub_p.text == expected_p
        assert sub_s.text == expected_s

def to_tmp_time(time: int) -> int:
    """
    Helper to convert time from milliseconds to seconds used in TMP format.

    Args:
        time (int): Time in milliseconds.

    Returns:
        int: Time in seconds (floored to nearest lower integer).
    """
    return floor(time / 1000)
