"""
Subtitle loader module for reading and parsing subtitle files and edit data.

This module provides functions to load primary and secondary subtitles, parse and 
tokenize secondary subtitle content, and load subtitle edit files with style and token 
information. It supports both plain and compressed formats.

Dependencies:
    - pysubs2: For subtitle file parsing and style handling.
    - charset_normalizer: For robust encoding detection.
"""

import gzip
import json
from pathlib import Path
from typing import Union

import pysubs2
from charset_normalizer import from_path

from duosubs.subtitle.data import SubtitleData
from duosubs.subtitle.field import SubtitleField
from duosubs.subtitle.tokenizer import SubtitleTokenizer

from .utils import _decode, _deserialize_styles


def load_subs(subtitle_path: Union[Path, str]) -> SubtitleData:
    """
    Loads subtitles, tokenizes sentences, and extracts style and token information.

    Args:
        subtitle_path (Path | str): Path to the subtitle file.

    Returns:
        SubtitleData:
        - List of SubtitleField objects for each subtitle event. (list[SubtitleField])
        - SSAFile object containing style information. (pysubs2.SSAFile)
        - List of tokenized sentences from the subtitles. (list[str])
        - List of style tokens corresponding to each sentence. (list[str])
    """
    pysub2_subs = _load_to_pysub2(Path(subtitle_path))
    pysub2_subs.sort()

    styles = pysubs2.SSAFile()
    styles.import_styles(pysub2_subs)

    pattern = SubtitleTokenizer.detect_regex_pattern(pysub2_subs)
    subs = []
    tokens = []
    styles_tokens = []
    for content in pysub2_subs:
        sentences = SubtitleTokenizer.tokenize_sentence(
            pattern, content.text.replace("\\N", "\n")
        )
        tokens.extend(sentences)
        index_start = len(tokens) - len(sentences)
        index_end = len(tokens)
        styles_tokens += [content.style for _ in range(len(sentences))]
        subs.append(
            SubtitleField(
                start = content.start,
                end = content.end,
                primary_text = content.text,
                primary_token_spans=(index_start, index_end),
                primary_style = content.style
            )
        )

    subs_data = SubtitleData(
        subs=subs,
        styles=styles,
        tokens=tokens,
        styles_tokens=styles_tokens
    )
    return subs_data

def load_file_edit(
        file_path: Union[Path, str]
    ) -> tuple[list[SubtitleField], pysubs2.SSAFile, pysubs2.SSAFile]:
    """
    Loads a compressed subtitle edit file, including subtitle fields and style 
    information.

    Args:
        file_path (Path | str): Path to the compressed edit file (.json.gz).

    Returns:
        tuple[list[SubtitleField], pysubs2.SSAFile, pysubs2.SSAFile]:
        - List of SubtitleField objects representing the subtitles.
        - SSAFile object containing primary styles.
        - SSAFile object containing secondary styles.
    """
    with gzip.open(file_path, "rt", encoding="utf-8") as file:
        data = _decode(json.load(file))

    ssa1_styles = _deserialize_styles(data["primary_styles"])
    ssa2_styles = _deserialize_styles(data["secondary_styles"])
    subtitles = [SubtitleField(**s) for s in data["subtitles"]]

    primary_styles = pysubs2.SSAFile()
    secondary_styles = pysubs2.SSAFile()

    primary_styles.styles = ssa1_styles.copy()
    secondary_styles.styles = ssa2_styles.copy()

    return subtitles, primary_styles, secondary_styles

def _load_to_pysub2(path: Path) -> pysubs2.SSAFile:
    """
    Loads a subtitle file into a pysubs2.SSAFile object, using detected encoding.

    Args:
        path (str): Path to the subtitle file.

    Returns:
        pysubs2.SSAFile: Parsed subtitle file object.

    Raises:
        ValueError: If encoding cannot be detected.
    """
    match = from_path(path).best()
    if match is not None:
        encoding = match.encoding
    else:
        raise ValueError(f"Could not detect encoding for file: {path}")
    return pysubs2.load(str(path), encoding)
