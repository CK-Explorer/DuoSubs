"""
Data model for a single subtitle field, including timing, text, style, and alignment 
information.

This module defines the SubtitleField dataclass, which is used to represent a single 
subtitle event with both primary and secondary language content, timing, style, and 
alignment score.
"""

from dataclasses import dataclass


@dataclass
class SubtitleField:
    """
    Represents a single subtitle event with timing, text, style, and alignment score.

    Attributes:
        start (int): Start time of the primary subtitle in milliseconds. Defaults to -1.
        end (int): End time of the primary subtitle in milliseconds. Defaults to -1.
        secondary_token_spans (tuple[int, int]): Tuple indicating the start and end 
            token indices for the tokenized secondary subtitle. Defaults to (-1, -1).
        primary_text (str): Text content of the primary subtitle. Defaults to an empty 
            string.
        secondary_text (str): Text content of the secondary subtitle. Defaults to an 
            empty string.
        score (float): Alignment or similarity score between primary and secondary 
            subtitles. Defaults to -1.0.
        primary_style (str): Style name for the primary subtitle. Defaults to "Default".
        secondary_style (str): Style name for the secondary subtitle. Defaults to 
            "Default".
    """

    start: int = -1
    end: int = -1
    primary_token_spans: tuple[int, int] = (-1, -1)
    secondary_token_spans: tuple[int, int] = (-1, -1)
    primary_text: str = ""
    secondary_text: str = ""
    score: float = -1.0
    primary_style: str = "Default"
    secondary_style: str = "Default"

    def __lt__(self, other: "SubtitleField") -> bool:
        """
        Compare SubtitleField objects by their start time for sorting.

        Args:
            other (SubtitleField): Another SubtitleField instance to compare with.

        Returns:
            bool: True if this instance starts before the other, False otherwise.
        """
        return self.start < other.start
