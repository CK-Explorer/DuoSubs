"""
Constants for supported subtitle file extensions stated in duosubs.common.enums and 
language codes.

This module defines lists of supported subtitle file extensions for time-based and 
native formats, as well as a list of ISO 639-1 language codes for non-space-separated 
languages.
"""

from .enums import SubtitleFormat

SUPPORTED_SUB_EXT: list[str] = [f.value for f in SubtitleFormat]

SUPPORTED_NATIVE_SUB_EXT: list[str] = [
    "ass",
    "ssa"
]

SUPPORTED_TIME_BASED_SUB_EXT: list[str] = list(
    set(SUPPORTED_SUB_EXT) - set(SUPPORTED_NATIVE_SUB_EXT)
)

NON_SPACE_SEPARATED_ISO639_1: list[str] = [
    "ZH",  # Chinese
    "JA",  # Japanese
    "TH",  # Thai
    "LO",  # Lao (Not supported yet by Lingua)
    "MY",  # Burmese (Not supported yet by Lingua)
    "KM",  # Khmer (Not supported yet by Lingua)
    "BO",  # Tibetan (Not supported yet by Lingua)
    "JV",  # Javanese (Not supported yet by Lingua)
    "SI",  # Sinhala (Not supported yet by Lingua)
    "DZ",  # Dzongkha (Not supported yet by Lingua)
]
