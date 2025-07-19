"""
Unit tests for subtitle tokenization logic in 
duosubs.subtitle.tokenizer.SubtitleTokenizer.

This module contains pytest-based unit tests for regex pattern detection, sentence 
tokenization, leading dash combination, and language code detection in 
SubtitleTokenizer.
"""

from pathlib import Path
from typing import TypedDict, cast
from unittest.mock import MagicMock, patch

import pytest
from pysubs2 import SSAEvent, SSAFile

from duosubs.subtitle.tokenizer import SubtitleTokenizer
from tests.common_utils.utils import load_test_cases

# pylint: disable=protected-access
# Test cases paths
DATA_PATH: Path = Path(__file__).parent / "data"
DATA_TOKENIZE_SENTENCE: Path = DATA_PATH / "tokenize_sentence.yaml"
DATA_COMBINE_LEADING_DASH: Path = DATA_PATH / "combine_leading_dash.yaml"

# ----------------------------
# TypedDict Definitions for Tests
# ----------------------------

class TokenizeSentence(TypedDict):
    """
    Represents a test case for the tokenize_sentence function.

    Attributes:
        text (str): Input text to be tokenized.
        expected (list[str]): Expected list of tokenized sentences.
        language (str): Language code for the input text.
    """
    text: str
    expected: list[str]
    language: str

class CombineLeadingDash(TypedDict):
    """
    Represents a test case for the _combine_leading_dash function.

    Attributes:
        input (str): Input text with leading dashes.
        expected (str): Expected output after combining leading dashes.
    """
    input: list[str]
    expected: list[str]

# ----------------------------
# Regex Pattern Detection Tests
# ----------------------------

def test_detect_regex_pattern_for_non_space_language() -> None:
    """
    Test that detect_regex_pattern function includes whitespace for non-space-separated 
    languages.
    """
    subs = SSAFile()
    subs.events.append(SSAEvent(start=0, end=1000, text="你好，世界")) # noqa: RUF001

    with patch.object(SubtitleTokenizer, "_detect_language_code", return_value="zh"):
        pattern = SubtitleTokenizer.detect_regex_pattern(subs)

    assert pattern.pattern.startswith(r"([")
    assert r"\s+" in pattern.pattern or r"\s*" in pattern.pattern

def test_detect_regex_pattern_for_space_language() -> None:
    """
    Test that detect_regex_pattern functiondoes not include whitespace for 
    space-separated languages.
    """
    subs = SSAFile()
    subs.events.append(SSAEvent(start=0, end=1000, text="Hello world."))

    with patch.object(SubtitleTokenizer, "_detect_language_code", return_value="en"):
        pattern = SubtitleTokenizer.detect_regex_pattern(subs)

    assert pattern.pattern.startswith(r"([")
    assert r"\s+" not in pattern.pattern.split(")")[0]

def test_detect_regex_pattern_none_detected() -> None:
    """
    Test that detect_regex_pattern function falls back to non-space-separator rule if 
    language is not detected.
    """
    subs = SSAFile()
    with patch.object(SubtitleTokenizer, "_detect_language_code", return_value=None):
        pattern = SubtitleTokenizer.detect_regex_pattern(subs)

    # Fallback to non-space-separator rule
    assert r"\s+" in pattern.pattern or r"\s*" in pattern.pattern

# ----------------------------
# Tokenize Sentence Tests
# ----------------------------

@pytest.mark.parametrize(
    "case",
    cast(list[TokenizeSentence], load_test_cases(DATA_TOKENIZE_SENTENCE))
)
def test_tokenize_sentence(case: TokenizeSentence) -> None:
    """
    Test tokenize_sentence function for sentence tokenization for various languages and 
    input cases.

    Args:
        case (TokenizeSentence): Test case data loaded from YAML.
    """
    subs = SSAFile()
    subs.events.append(SSAEvent(start=0, end=1000, text=case["text"]))

    with patch.object(
        SubtitleTokenizer,
        "_detect_language_code",
        return_value=case["language"]
    ):
        pattern = SubtitleTokenizer.detect_regex_pattern(subs)
        result = [
            SubtitleTokenizer.tokenize_sentence(pattern, sub.text) for sub in subs
        ]

    assert result[0] == case["expected"]

# ----------------------------
# Combine Leading Dash Tests
# ----------------------------

@pytest.mark.parametrize(
    "case",
    cast(list[CombineLeadingDash], load_test_cases(DATA_COMBINE_LEADING_DASH))
)
def test_combine_leading_dash(case: CombineLeadingDash) -> None:
    """
    Test _combine_leading_dash function for leading dash combination logic for dialogue 
    lines.

    Args:
        case (CombineLeadingDash): Test case data loaded from YAML.
    """
    assert SubtitleTokenizer._combine_leading_dash(case["input"]) == case["expected"]

# ----------------------------
# Language Code Detection Tests
# ----------------------------

def test_detect_language_code_mocked() -> None:
    """
    Test _detect_language_code function with a mocked language detector returning a 
    valid ISO code.
    """
    subs = SSAFile()
    subs.events.append(SSAEvent(start=0, end=1000, text="Hello World"))

    mock_language = MagicMock()
    mock_language.iso_code_639_1 = "IsoCode639_1.en"

    with patch("duosubs.subtitle.tokenizer.LanguageDetectorBuilder") as mock_builder:
        builder = mock_builder.from_all_languages.return_value
        low_acc = builder.with_low_accuracy_mode.return_value
        mock_detector = low_acc.build.return_value

        mock_detector.detect_language_of.return_value = mock_language
        mock_detector.unload_language_models.return_value = None

        result = SubtitleTokenizer._detect_language_code(subs)
        assert result == "en"

def test_detect_language_code_no_iso() -> None:
    """
    Test _detect_language_code function with a mocked language detector returning None.
    """
    subs = SSAFile()
    subs.events.append(SSAEvent(start=0, end=1000, text="Some text"))

    with patch("duosubs.subtitle.tokenizer.LanguageDetectorBuilder") as mock_builder:
        builder = mock_builder.from_all_languages.return_value
        low_acc = builder.with_low_accuracy_mode.return_value
        mock_detector = low_acc.build.return_value

        mock_detector.detect_language_of.return_value = None
        mock_detector.unload_language_models.return_value = None

        result = SubtitleTokenizer._detect_language_code(subs)
        assert result is None

def test_detect_language_code_empty() -> None:
    """
    Test _detect_language_code function with an empty subtitle file.
    """
    subs = SSAFile()
    with patch("duosubs.subtitle.tokenizer.LanguageDetectorBuilder") as mock_builder:
        builder = mock_builder.from_all_languages.return_value
        low_acc = builder.with_low_accuracy_mode.return_value
        mock_detector = low_acc.build.return_value

        mock_detector.detect_language_of.return_value = None
        mock_detector.unload_language_models.return_value = None

        result = SubtitleTokenizer._detect_language_code(subs)
        assert result is None
