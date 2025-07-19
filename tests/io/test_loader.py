"""
Unit tests for subtitle loader functions in duosubs.io.loader.

This module contains pytest-based unit tests for loading primary, secondary, and edit 
subtitle files, verifying correct parsing, tokenization, and style extraction.
"""

from math import isclose
from pathlib import Path
from typing import TypedDict, cast

import pysubs2
import pytest

from duosubs.io.loader import load_file_edit, load_subs
from duosubs.subtitle.field import SubtitleField
from tests.common_utils.utils import SubtitleFieldDict, load_test_cases

# Test subtitle paths
SUB_PATH: Path = Path(__file__).parent / "sub_data"
TEST_SUB_PATH: Path = SUB_PATH / "TOS-en-trimmed.ass"
TEST_SUB_COMPRESSED_PATH: Path = SUB_PATH / "TOS-en-cht-trimmed.json.gz"

# Test cases paths
DATA_PATH: Path = Path(__file__).parent / "data"
DATA_SUBS_IN_SUBS_FIELD: Path = DATA_PATH / "subs_in_subtitle_field.yaml"
DATA_FILE_EDIT_SUBS_FIELD: Path = DATA_PATH / "file_edit_subtitle_field.yaml"

# ----------------------------
# TypedDict Definitions for Tests
# ----------------------------

class SubsInSubsFieldTest(TypedDict):
    """
    Represents the results to be verified for the load_subs function.

    Attributes:
        subs (list[SubtitleFieldDict]): Input subtitles.
        tokens (list[str]): List of tokenized sentences from the subtitles.
        styles_tokens (str): Style tokens corresponding to each tokens.
    """
    subs: list[SubtitleFieldDict]
    tokens: list[str]
    styles_tokens: str

class FileEditSubsFieldTest(TypedDict):
    """
    Represents the results to be verified for the load_file_edit function.

    Attributes:
        subs (list[SubtitleFieldDict]): Input subtitles.
    """
    subs: list[SubtitleFieldDict]

# ------------------------
# Subtitle Loading Tests
# ------------------------

@pytest.mark.parametrize(
    "case",
    cast(list[SubsInSubsFieldTest], load_test_cases(DATA_SUBS_IN_SUBS_FIELD))
)
def test_load_subs(case: SubsInSubsFieldTest) -> None:
    """
    Test load_subs function for loading and tokenizing subtitles, and extracting style
    tokens.

    Args:
        case (SubsInSubsFieldTest): Test case data loaded from YAML.
    """
    subs_data = load_subs(TEST_SUB_PATH)
    expected_subs = [SubtitleField(**s) for s in case["subs"]]
    for sub in expected_subs:
        a, b = sub.primary_token_spans
        sub.primary_token_spans = (a, b)

    assert subs_data.subs == expected_subs
    assert subs_data.tokens == case["tokens"]
    for style in subs_data.styles_tokens:
        assert style == case["styles_tokens"]
    assert isinstance(subs_data.styles, pysubs2.SSAFile)
    assert "English" in subs_data.styles.styles

# ------------------------
# File Edit Loading Tests
# ------------------------

@pytest.mark.parametrize(
    "data",
    cast(list[FileEditSubsFieldTest], load_test_cases(DATA_FILE_EDIT_SUBS_FIELD))
)
def test_load_file_edit(data: FileEditSubsFieldTest) -> None:
    """
    Test load_file_edit for loading subtitle edit files and verifying subtitle and style
    content.

    Args:
        data (FileEditSubsFieldTest): Test case data loaded from YAML.
    """
    (
        output_subs,
        primary_styles,
        secondary_styles
    ) = load_file_edit(TEST_SUB_COMPRESSED_PATH)
    expected_subs = [SubtitleField(**s) for s in data["subs"]]

    assert len(output_subs) == len(expected_subs)
    for actual, expected in zip(output_subs, expected_subs, strict=False):
        assert actual.start == expected.start
        assert actual.end == expected.end
        assert actual.primary_text == expected.primary_text
        assert actual.secondary_text == expected.secondary_text
        assert isclose(actual.score, expected.score, rel_tol=1e-4, abs_tol=1e-4)
        assert actual.primary_style == expected.primary_style
        assert actual.secondary_style == expected.secondary_style

    assert isinstance(primary_styles, pysubs2.SSAFile)
    assert "Default" in primary_styles.styles
    assert isinstance(secondary_styles, pysubs2.SSAFile)
    assert "Default" in secondary_styles.styles
