"""
Subtitle data container for subtitles, and their tokenized as well as style information.

This module defines the SubtitleData dataclass, which stores subtitle fields, style 
information, tokenized sentences, and style tokens for use in merging and alignment 
routines.

Exports:
    SubtitleData: Dataclass container for subtitle fields, styles, tokens, and style 
        tokens.
"""

from dataclasses import dataclass, field

import pysubs2

from .field import SubtitleField


@dataclass
class SubtitleData:
    """
    Container for subtitle fields, style information, tokenized sentences, and style 
    tokens.

    Attributes:
        subs (list[SubtitleField]): List of subtitle field objects.
        styles (pysubs2.SSAFile): SSAFile object containing style information.
        tokens (list[str]): List of tokenized sentences from the subtitles.
        styles_tokens (list[str]): List of style tokens corresponding to each sentence.
    """

    subs: list[SubtitleField] = field(default_factory=list)
    styles: pysubs2.SSAFile = field(default_factory=pysubs2.SSAFile)
    tokens: list[str] = field(default_factory=list)
    styles_tokens: list[str] = field(default_factory=list)
