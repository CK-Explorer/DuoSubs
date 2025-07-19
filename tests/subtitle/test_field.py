"""
Unit tests for the SubtitleField dataclass in duosubs.subtitle.field.

This module contains tests for equality and sorting for SubtitleField.
"""

from duosubs.subtitle.field import SubtitleField

# ----------------------------
# Equality and Sorting
# ----------------------------

def test_subtitle_field_equality() -> None:
    """
    Test equality comparison between SubtitleField instances.
    """
    a = SubtitleField(start=1, end=2, primary_text="A", score=0.5)
    b = SubtitleField(start=1, end=2, primary_text="A", score=0.5)
    c = SubtitleField(start=1, end=2, primary_text="B", score=0.5)

    assert a == b
    assert a != c

def test_subtitle_field_sorting() -> None:
    """
    Test sorting of SubtitleField instances by start time.
    """
    a = SubtitleField(start=300)
    b = SubtitleField(start=100)
    c = SubtitleField(start=200)
    sorted_list = sorted([a, b, c])
    assert [sub.start for sub in sorted_list] == [100, 200, 300]
