"""
Test utilities for loading YAML-based test cases and defining test data structures.

This module provides:
    - A helper function to load test cases from a YAML file for use in unit tests or 
        validation routines.
    - TypedDict definitions for structured test data, such as subtitle fields.
"""

import re
from pathlib import Path
from typing import Any, TypedDict

import yaml

# ----------------------------
# Util Functions
# ----------------------------

def load_test_cases(path: Path) -> Any:
    """
    Load test cases from a YAML file.

    Args:
        path (Path): Path to the YAML file containing test cases.

    Returns:
        Any: Parsed test cases from the YAML file. The structure depends on the file 
            contents.
    """
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)
    
def strip_ansi(text: str) -> str:
    """
    Remove ANSI color and formatting codes, such as those used in terminal
    output for colored text.

    Args:
        text (str): The input string that may contain ANSI escape codes.

    Returns:
        str: The input string with ANSI codes removed.
    """
    return re.sub(r"\x1B\[[0-?]*[ -/]*[@-~]", "", text)

# ----------------------------
# TypedDict Definitions for Tests
# ----------------------------

class SubtitleFieldDict(TypedDict):
    """
    TypedDict for representing a subtitle field in test cases.

    Attributes:
        start (int): Start time in milliseconds.
        end (int): End time in milliseconds.
        secondary_token_spans (tuple[int, int]): Tuple indicating the start and end 
            token indices for the tokenized secondary subtitle.
        primary_text (str): Primary language subtitle text.
        secondary_text (str): Secondary language subtitle text.
        score (float): Alignment or similarity score.
        primary_style (str): Style name for the primary subtitle.
        secondary_style (str): Style name for the secondary subtitle.
    """
    start: int
    end: int
    secondary_token_spans: tuple[int, int]
    primary_text: str
    secondary_text: str
    score: float
    primary_style: str
    secondary_style: str
