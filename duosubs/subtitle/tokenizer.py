"""
Subtitle tokenizer module for tokenizing the text inside the subtitle files.

This module provides the SubtitleTokenizer class, which can detect the language of 
subtitle files and split subtitle text into smaller chunks of sentences or tokens. 

It supports special handling for non-space-separated languages and dialogue formatting.

Dependencies:
    - pysubs2: For subtitle file parsing.
    - lingua: For language detection.
"""

import re
from typing import Optional, Pattern

import pysubs2
from lingua import LanguageDetectorBuilder

from duosubs.common.constants import NON_SPACE_SEPARATED_ISO639_1


class SubtitleTokenizer:
    """
    A tokenizer class for pre-processing subtitle files, by detecting language and 
    splitting text into sentences or tokens.
    """
    @staticmethod
    def detect_regex_pattern(subs: pysubs2.SSAFile) -> Pattern[str]:
        """
        Detects and returns a regex pattern for sentence tokenization based on the 
        detected language of the subtitles.
        For non-space-separated languages, includes whitespace in the split pattern.
        
        Args:
            subs (pysubs2.SSAFile): The subtitle file object.
        
        Returns:
            Pattern[str]: The compiled regex pattern for sentence splitting.
        """
        language_code = SubtitleTokenizer._detect_language_code(subs)

        if (
            not language_code
            or language_code.upper() in NON_SPACE_SEPARATED_ISO639_1
        ):
            pattern = r"([。！？!?，、・,،;٫؛:：…｡\.!\?॥।።။།៕፣؟\n\r\s]+)\s*" # noqa: RUF001
        else:
            pattern = r"([。！？!?，、・,،;٫؛:：…｡\.!\?॥।።။།៕፣؟\n\r]+)\s*" # noqa: RUF001

        return re.compile(pattern)

    @staticmethod
    def tokenize_sentence(pattern: Pattern[str], text: str) -> list[str]:
        """
        Splits the input text into a list of sentence tokens using the provided regex 
        pattern. Also combines leading dash lines (e.g., for dialogue).
        
        Args:
            pattern (Pattern[str]): The regex pattern for splitting sentences.
            text (str): The text to tokenize.
        
        Returns:
            list[str]: The list of sentence tokens.
        """
        parts = pattern.split(text)
        tokens = [
            "".join(pair).replace("\n", "\\N").strip() 
            for pair in zip(parts[::2], parts[1::2], strict=False)
        ]
        if parts[::2][-1]:
            tokens.append(parts[-1])
        tokens = SubtitleTokenizer._combine_leading_dash(tokens)
        return tokens

    @staticmethod
    def _combine_leading_dash(text_list: list[str]) -> list[str]:
        """
        Combines lines that start with a dash ("-") with the following line, typically 
        used for dialogue formatting.
        
        Args:
            text_list (list[str]): The list of text segments.
        
        Returns:
            list[str]: The processed list with leading dashes combined.
        """
        skip = False
        result = []

        for idx,_ in enumerate(text_list):
            if skip:
                skip = False
                continue

            if text_list[idx] == "-" and idx + 1 < len(text_list):
                result.append(text_list[idx] + " " + text_list[idx + 1])
                skip = True
            else:
                result.append(text_list[idx])

        return result

    @staticmethod
    def _detect_language_code(subs: pysubs2.SSAFile) -> Optional[str]:
        """
        Detects the ISO 639-1 language code of the subtitle file using the Lingua 
        language detector.
        
        Args:
            subs (pysubs2.SSAFile): The subtitle file object.
        
        Returns:
            Optional[str]: The detected ISO 639-1 language code, or None if detection 
                fails.
        """
        full_text = " ".join([line.text.replace("\\N", " ") for line in subs])
        all_language_detector_builder = LanguageDetectorBuilder.from_all_languages()
        detector = all_language_detector_builder.with_low_accuracy_mode().build()
        language = detector.detect_language_of(full_text)
        language_code = (
            str(language.iso_code_639_1).replace("IsoCode639_1.", "")
            if language else None
        )
        detector.unload_language_models() # type: ignore[no-untyped-call]
        return language_code
