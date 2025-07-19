"""
Unit tests for subtitle merging logic in duosubs.core.merger.Merger.

This module contains pytest-based unit tests for the merging, alignment, and utility 
functions of Merger, including helpers for score simulation and result comparison.
"""
from math import isclose
from pathlib import Path
from typing import Any, Callable, TypedDict, cast
from unittest.mock import patch

import pytest
import torch
from sentence_transformers import SentenceTransformer

from duosubs.core.merger import Merger
from duosubs.subtitle.data import SubtitleData
from duosubs.subtitle.field import SubtitleField
from tests.common_utils.utils import SubtitleFieldDict, load_test_cases

# pylint: disable=protected-access
# Test cases paths
DATA_PATH: Path = Path(__file__).parent / "data"
DATA_ALIGN_SUBS_NEIGHBOUR: Path = DATA_PATH / "align_subs_neighbour.yaml"
DATA_ELIMINATE_NEWLINE: Path = DATA_PATH / "eliminate_unnecessary_newline.yaml"
DATA_ALIGN_SUBS_WITH_SEC_TOKENS: Path = DATA_PATH / "align_subs_with_sec_tokens.yaml"
DATA_EXTRACT_FILTER_NON_OVERLAP: Path = DATA_PATH / "extract_filter_non_overlap.yaml"
DATA_FILTER_TOKEN_SPANS: Path = DATA_PATH / "filter_token_spans.yaml"
DATA_FILTER_TOKENS_AND_STYLES: Path = DATA_PATH / "filter_tokens_and_styles.yaml"
DATA_GENERATE_ALL_COMBINATIONS: Path =(
    DATA_PATH / "generate_all_consecutive_combinations.yaml"
)
DATA_GET_PROGRESS_PERCENTAGE: Path =  DATA_PATH / "get_progress_percentage.yaml"

# ----------------------------
# TypedDict Definitions for Tests
# ----------------------------

class ScorePair(TypedDict):
    """
    Represents a pair of scores for interleaved merging tests.

    Attributes:
        left (list[list[float]]): Scores for left subtitles.
        right (list[list[float]]): Scores for right subtitles.
    """
    left: list[list[float]]
    right: list[list[float]]

class AlignSubsNeighbourTest(TypedDict):
    """
    Represents a test case for the align_subs_using_neighbours function.

    Attributes:
        name (str): Name of the test case.
        subtitle_window_size (int): Window size for refinement.
        subs (list[SubtitleFieldDict]): Subtitles to refine.
        secondary_tokens (list[str]): Secondary tokens.
        secondary_styles_tokens (list[str]): Secondary style tokens.
        scores (list[ScorePair]): Score pairs for alignment.
        expected_subs (list[SubtitleFieldDict]): Expected subtitles after alignment.
    """
    name: str
    subtitle_window_size: int
    subs: list[SubtitleFieldDict]
    secondary_tokens: list[str]
    secondary_styles_tokens: list[str]
    scores: list[ScorePair]
    expected_subs: list[SubtitleFieldDict]

class EliminateNewlineTest(TypedDict):
    """
    Represents a test case for the eliminate_unnecessary_newline function.

    Attributes:
        text (str): Input text with newlines.
        expected (str): Expected text after newline elimination.
    """
    text: str
    expected: str

class AlignSubsWithSecTokensTest(TypedDict):
    """
    Represents a test case for the _align_subs_with_secondary_tokens function.

    Attributes:
        dtw_path (list[tuple[int, int]]): DTW path for alignment.
        primary_subs (list[SubtitleFieldDict]): Primary subtitles.
        secondary_tokens (list[str]): Secondary subtitles tokens.
        secondary_styles_tokens (list[str]): Style for each tokens from secondary 
            subtitles.
        expected_subs (list[SubtitleFieldDict]): Expected subtitles after alignment.
    """
    dtw_path: list[tuple[int, int]]
    primary_subs: list[SubtitleFieldDict]
    secondary_tokens: list[str]
    secondary_styles_tokens: list[str]
    expected_subs: list[SubtitleFieldDict]

class ExtractFilterNonOverlapTest(TypedDict):
    """
    Represents a test case for the _filter_and_extract_non_overlap_subs function.

    Attributes:
        name (str): Name of the test case.
        input_subs (list[SubtitleFieldDict]): Input subtitles.
        ref_subs (list[SubtitleFieldDict]): Reference subtitles.
        expected_token_spans (list[tuple[int, int]]): Expected token spans.
        expected_primary (list[SubtitleFieldDict]): Expected primary subtitles.
        expected_secondary (list[SubtitleFieldDict]): Expected secondary subtitles.
        expected_input_subs (list[SubtitleFieldDict]): Expected input subtitles after 
            filtering.
    """
    name: str
    input_subs: list[SubtitleFieldDict]
    ref_subs: list[SubtitleFieldDict]
    expected_token_spans: list[tuple[int, int]]
    expected_primary: list[SubtitleFieldDict]
    expected_secondary: list[SubtitleFieldDict]
    expected_input_subs: list[SubtitleFieldDict]

class FilterTokenSpansTest(TypedDict):
    """
    Represents a test case for the _filter_token_spans function.

    Attributes:
        name (str): Name of the test case.
        input (list[tuple[int, int]]): Input token spans.
        expected (list[tuple[int, int]]): Expected token spans after filtering.
    """
    name: str
    input: list[tuple[int, int]]
    expected: list[tuple[int, int]]

class FilterTokensAndStylesTest(TypedDict):
    """
    Represents a test case for the _filter_tokens_and_styles function.

    Attributes:
        tokens (list[str]): Input tokens.
        styles (list[str]): Input styles.
        non_overlap_tokens_spans (list[tuple[int, int]]): Non-overlapping subtitles 
            token spans.
        expected_tokens (list[str]): Expected tokens after filtering.
        expected_styles (list[str]): Expected styles after filtering.
    """
    tokens: list[str]
    styles: list[str]
    non_overlap_tokens_spans: list[tuple[int, int]]
    expected_tokens: list[str]
    expected_styles: list[str]

class GenerateCombinationsTest(TypedDict):
    """
    Represents a test case for the _generate_all_consecutive_combinations function.

    Attributes:
        tokens (list[str]): List of tokens to generate combinations from.
        start: int: Start index for combinations.
        end: int: End index for combinations.
        expected_combos (list[str]): Expected combinations of tokens.
        expected_indices (list[tuple[int, int]]): Expected start and end indices for 
            each combination.
    """
    tokens: list[str]
    start: int
    end: int
    expected_combos: list[str]
    expected_indices: list[tuple[int, int]]

class GetProgressPercentageTest(TypedDict):
    """
    Represents a test case for the _get_progress_percentage function.

    Attributes:
        index (int): Current index in the process.
        total_index (int): Total number of items to process.
        ratio (int): Ratio of progress.
        previous_ratio (list[int]): Previous ratios for comparison.
        expected (int): Expected percentage of progress.
    """
    index: int
    total_index: int
    ratio: int
    previous_ratio: list[int]
    expected: int

# ----------------------------
# Merging Functions Tests
# ----------------------------

@pytest.mark.parametrize(
    "case", 
    cast(list[AlignSubsNeighbourTest], load_test_cases(DATA_ALIGN_SUBS_NEIGHBOUR))
)
@pytest.mark.parametrize("stop", [True, False])
def test_align_subs_using_neighbours(case: AlignSubsNeighbourTest, stop: bool) -> None:
    """
    Test the align_subs_using_neighbours function for subtitle alignment refinement and
    early stopping.

    Args:
        case (AlignSubsNeighbourTest): Test case data loaded from YAML.
        stop (bool): Whether to simulate early stopping.
    """
    score_pairs = []
    for pair in case["scores"]:
        left = torch.tensor(pair["left"])
        right = torch.tensor(pair["right"])
        score_pairs.append((left, right))

    dummy_score_fn = make_interleaved_score(score_pairs)

    with patch("duosubs.core.merger.Merger._compute_score",
               side_effect=dummy_score_fn
    ):
        subs = [SubtitleField(**s) for s in case["subs"]]
        secondary_subs_data = SubtitleData(
            tokens=case["secondary_tokens"],
            styles_tokens=case["secondary_styles_tokens"]
        )
        merger = Merger(
            SubtitleData(),
            secondary_subs_data
        )
        stop_bit = [True] if stop else [False]
        stage_number = 0
        dummy_model = cast(SentenceTransformer, DummyModel())
        output_subs, stage_number = merger.align_subs_using_neighbours(
            subs, case["subtitle_window_size"], dummy_model, stage_number, stop_bit
        )
        expected_subs = (
            [SubtitleField(**s) for s in case["subs"]] if stop
            else [SubtitleField(**s) for s in case["expected_subs"]]
        )
        assert stage_number == 1
        assert_subtitle_fields_equal(output_subs, expected_subs)

@pytest.mark.parametrize(
    "case",
    cast(list[EliminateNewlineTest], load_test_cases(DATA_ELIMINATE_NEWLINE))
)
@pytest.mark.parametrize("stop", [True, False])
def test_eliminate_unnecessary_newline(
        case: EliminateNewlineTest,
        stop: bool
    ) -> None:
    """
    Test the eliminate_unnecessary_newline function for cleaning up newlines in 
    subtitles and early stopping.

    Args:
        case (EliminateNewlineTest): Test case data loaded from YAML.
        stop (bool): Whether to simulate early stopping.
    """
    stop_bit = [True] if stop else [False]
    sub = SubtitleField(
        primary_text=case["text"],
        secondary_text=case["text"]
    )
    merger = Merger(SubtitleData(), SubtitleData())
    result = merger.eliminate_unnecessary_newline([sub], stop_bit)
    if stop:
        assert result[0].primary_text == case["text"]
        assert result[0].secondary_text == case["text"]
    else:
        assert result[0].primary_text == case["expected"]
        assert result[0].secondary_text == case["expected"]

@pytest.mark.parametrize(
    "case",
    cast(
        list[AlignSubsWithSecTokensTest],
        load_test_cases(DATA_ALIGN_SUBS_WITH_SEC_TOKENS)
    )
)
def test_align_subs_with_secondary_tokens(case: AlignSubsWithSecTokensTest) -> None:
    """
    Test the _align_subs_with_secondary_tokens function for correct alignment with 
    secondary tokens, based on DTW path provided.

    Args:
        case (AlignSubsWithSecTokensTest): Test case data loaded from YAML.
    """
    primary_subs = [SubtitleField(**s) for s in case["primary_subs"]]
    primary_subs_data = SubtitleData(subs=primary_subs)
    secondary_subs_data = SubtitleData(
        tokens=case["secondary_tokens"],
        styles_tokens=case["secondary_styles_tokens"]
    )
    merger = Merger(primary_subs_data, secondary_subs_data)
    output_subs = merger._align_subs_with_secondary_tokens(case["dtw_path"])
    expected_subs = [SubtitleField(**s) for s in case["expected_subs"]]

    assert_subtitle_fields_equal(output_subs, expected_subs)

@pytest.mark.parametrize(
    "case",
    cast(
        list[ExtractFilterNonOverlapTest],
        load_test_cases(DATA_EXTRACT_FILTER_NON_OVERLAP)
    )
)
@pytest.mark.parametrize("input_is_primary", [True, False])
def test_filter_and_extract_non_overlap_subs(
        case: ExtractFilterNonOverlapTest,
        input_is_primary: bool
    ) -> None:
    """
    Test the _filter_and_extract_non_overlap_subs function for filtering out 
    non-overlapping subtitles from the input subtitles, and extracting the
    non-overlapping subtitles with their corresponding token spans.

    Args:
        case (NonOverlapMergeTest): Test case data loaded from YAML.
        stop (bool): Whether to simulate early stopping.
    """
    input_subs = [SubtitleField(**s) for s in case["input_subs"]]
    for sub in input_subs:
        a, b = sub.primary_token_spans
        sub.primary_token_spans = (a, b)
    ref_subs = [SubtitleField(**s) for s in case["ref_subs"]]

    output_subs, output_token_spans = Merger._filter_and_extract_non_overlap_subs(
        input_subs,
        ref_subs,
        input_is_primary
    )
    input_subs.sort()
    output_subs.sort()
    output_token_spans.sort()

    expected_subs = (
        [SubtitleField(**s) for s in case["expected_primary"]]
        if input_is_primary
        else [SubtitleField(**s) for s in case["expected_secondary"]]
    )
    expected_input_subs = [SubtitleField(**s) for s in case["expected_input_subs"]]
    expected_token_spans = [tuple(spans) for spans in case["expected_token_spans"]]

    assert_subtitle_fields_equal(output_subs, expected_subs)
    assert_subtitle_fields_equal(input_subs, expected_input_subs)
    assert output_token_spans == expected_token_spans

@pytest.mark.parametrize(
        "case",
        cast(list[FilterTokenSpansTest], load_test_cases(DATA_FILTER_TOKEN_SPANS))
    )
def test_filter_token_spans(case: FilterTokenSpansTest) -> None:
    """
    Test the _filter_token_spans function for correct filtering of token spans.

    Args:
        case (FilterTokenSpansTest): Test case data loaded from YAML.
    """
    input_subs = [
        SubtitleField(primary_token_spans=(span[0], span[1]))
        for span in case["input"]
    ]
    output_subs = Merger._filter_token_spans(input_subs)

    expected_subs = [
        SubtitleField(primary_token_spans=(span[0], span[1]))
        for span in case["expected"]
    ]
    assert output_subs==expected_subs

@pytest.mark.parametrize(
        "case",
        cast(
            list[FilterTokensAndStylesTest],
            load_test_cases(DATA_FILTER_TOKENS_AND_STYLES)
        )
    )
def test_filter_tokens_and_styles(case: FilterTokensAndStylesTest) -> None:
    """
    Test the _filter_tokens_and_styles function for correct filtering of tokens and 
    styles.

    Args:
        case (FilterTokensAndStylesTest): Test case data loaded from YAML.
    """
    output_tokens, output_styles = Merger._filter_tokens_and_styles(
        case["tokens"],
        case["styles"],
        case["non_overlap_tokens_spans"]
    )

    assert output_tokens == case["expected_tokens"]
    assert output_styles == case["expected_styles"]

@pytest.mark.parametrize(
    "case",
    cast(
        list[GenerateCombinationsTest],
        load_test_cases(DATA_GENERATE_ALL_COMBINATIONS)
    )
)
def test_generate_all_consecutive_combinations(case: GenerateCombinationsTest) -> None:
    """
    Test the _generate_all_consecutive_combinations function for correct token 
    combinations and indices.

    Args:
        case (GenerateCombinationsTest): Test case data loaded from YAML.
    """
    combos, indices = Merger._generate_all_consecutive_combinations(
        case["tokens"], case["start"], case["end"]
    )
    tuple_indices = [tuple(pair) for pair in case["expected_indices"]]
    assert combos == case["expected_combos"]
    assert indices == tuple_indices

# ----------------------------
# Utility Functions Tests
# ----------------------------

@pytest.mark.parametrize(
    "case", 
    cast(list[GetProgressPercentageTest], load_test_cases(DATA_GET_PROGRESS_PERCENTAGE))
)
def test_get_progress_percentage(case: GetProgressPercentageTest) -> None:
    """
    Test the _get_progress_percentage function for correct progress calculation.

    Args:
        case (GetProgressPercentageTest): Test case data loaded from YAML.
    """
    result = Merger._get_progress_percentage(
        case["index"], case["total_index"], case["ratio"], *case["previous_ratio"]
    )
    assert result == case["expected"]

# ------------------------
# Test Helpers / Stubs
# ------------------------

class DummyModel:
    """
    Dummy model for simulating sentence embedding output in tests.
    """
    def encode(
            self,
            texts: str,
            _convert_to_tensor: bool = True,
            **_kwargs: Any
        ) -> torch.Tensor:
        """
        Simulate encoding of input texts into random tensor embeddings.

        Args:
            texts (str): Input text(s) to encode.
            _convert_to_tensor (bool, optional): Ignored, for API compatibility.
            **_kwargs: Additional keyword arguments (ignored).

        Returns:
            torch.Tensor: Random tensor simulating sentence embeddings.
        """
        return torch.rand(len(texts), 384)

# ----------------------------
# Helper functions
# ----------------------------

def assert_subtitle_fields_equal(
        a: list[SubtitleField],
        b: list[SubtitleField]
    ) -> None:
    """
    Helper to assert equality of two lists of SubtitleField objects.

    Args:
        a (list[SubtitleField]): First list of subtitle fields.
        b (list[SubtitleField]): Second list of subtitle fields.
    """
    assert len(a) == len(b)
    for sub_a, sub_b in zip(a, b, strict=False):
        assert sub_a.start == sub_b.start
        assert sub_a.end == sub_b.end
        assert sub_a.primary_text == sub_b.primary_text
        assert sub_a.secondary_text == sub_b.secondary_text
        output_sub_token_spans = tuple(sub_a.secondary_token_spans)
        expected_sub_token_spans = tuple(sub_b.secondary_token_spans)
        assert output_sub_token_spans == expected_sub_token_spans
        assert isclose(sub_a.score, sub_b.score, rel_tol=1e-4, abs_tol=1e-4)
        assert sub_a.primary_style == sub_b.primary_style
        assert sub_a.secondary_style == sub_b.secondary_style

class Scorer:
    """
    Helper class to create a dummy score function that returns tensors in sequence.

    This class implements a callable that returns the next tensor from a predefined 
    list of tensors when called.
    """
    def __init__(self, scores: list[torch.Tensor]):
        self.iterator = iter(scores)

    def __call__(self, *_args: Any, **_kwargs: Any) -> torch.Tensor:
        return next(self.iterator)

def make_sequential_score(scores: list[torch.Tensor]) -> Callable[..., torch.Tensor]:
    """
    Helper to create a dummy score function that returns tensors in sequence.

    Args:
        scores (list[torch.Tensor]): List of tensors to return.

    Returns:
        Callable: Function that returns the next tensor on each call.
    """
    return Scorer(scores)

def make_interleaved_score(
        score_pairs: list[tuple[torch.Tensor, torch.Tensor]]
    ) -> Callable[..., torch.Tensor]:
    """
    Helper to create a dummy score function that returns tensors from pairs in 
    interleaved order.

    Args:
        score_pairs (list[tuple[torch.Tensor, torch.Tensor]]): List of (left, right) 
            tensor pairs.

    Returns:
        Callable: Function that returns the next tensor on each call.
    """
    flat_scores = [s for pair in score_pairs for s in pair]
    return Scorer(flat_scores)
