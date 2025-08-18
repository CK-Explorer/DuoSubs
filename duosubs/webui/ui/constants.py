"""
Constants used in the DuoSubs Web UI.

This module defines file paths, supported subtitle formats, model precision options,
merging mode options, and default values for use in the UI and other components.
"""

from pathlib import Path

from duosubs import MergingMode, ModelPrecision, SubtitleFormat

TITLE_HTML = Path(__file__).parent.parent / "assets" / "title.html"
MERGING_MODE_INFO = Path(__file__).parent.parent / "assets" / "merging_mode_info.html"

SUB_EXT_LIST: list[str] = [f.value for f in SubtitleFormat]
SUB_EXT_LIST_WITH_DOT: list[str] = [f".{ext}" for ext in SUB_EXT_LIST]
PRECISION_LIST: list[str] = [f.value for f in ModelPrecision]
MERGING_MODE_LIST: list[str] = [f.value.capitalize() for f in MergingMode]

DEFAULT_MODEL = "sentence-transformers/LaBSE"
DEFAULT_PRECISION = ModelPrecision.FLOAT32.value
DEFAULT_SUB_EXT = SubtitleFormat.ASS.value

SENTENCE_TRANSFORMER_URL = (
    "https://huggingface.co/models?library=sentence-transformers"
)
LEADERBOARD_URL = (
    "https://huggingface.co/spaces/mteb/leaderboard"
)
