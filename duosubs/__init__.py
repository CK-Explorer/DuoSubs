"""
duosubs package: Subtitle merging and alignment utilities.

This package provides the main API for semantic subtitle merging, including 
model/device selection, file loading, merging, saving, and error handling. It 
exposes core types, exceptions, and pipeline functions for both CLI and programmatic 
use.

Exports:
    - Enums: SubtitleFormat, OmitFile, DeviceType, ModelPrecision
    - Exceptions: LoadSubsError, LoadModelError, MergeSubsError, SaveSubsError
    - Types: MergeArgs, SubtitleData, SubtitleField
    - Pipeline: run_merge_pipeline, load_subtitles, load_sentence_transformer_model,
        merge_subtitles, save_subtitles
    - Merger: Merger
    - IO: load_subs, load_file_edit, save_file_edit, save_memory_edit, 
        save_file_combined, save_memory_combined, save_file_separate, 
        save_memory_separate
"""

from duosubs.common.enums import DeviceType, ModelPrecision, OmitFile, SubtitleFormat
from duosubs.common.exceptions import (
                                  LoadModelError,
                                  LoadSubsError,
                                  MergeSubsError,
                                  SaveSubsError,
)
from duosubs.common.types import MergeArgs
from duosubs.core.merge_pipeline import (
                                  load_sentence_transformer_model,
                                  load_subtitles,
                                  merge_subtitles,
                                  run_merge_pipeline,
                                  save_subtitles_in_zip,
)
from duosubs.core.merger import Merger
from duosubs.io.loader import load_file_edit, load_subs
from duosubs.io.writer import (
                                  save_file_combined,
                                  save_file_edit,
                                  save_file_separate,
                                  save_memory_combined,
                                  save_memory_edit,
                                  save_memory_separate,
)
from duosubs.subtitle.data import SubtitleData
from duosubs.subtitle.field import SubtitleField

__version__ = "0.2.0"

__all__ = [
    "DeviceType",
    "LoadModelError",
    "LoadSubsError",
    "MergeArgs",
    "MergeSubsError",
    "Merger",
    "ModelPrecision",
    "OmitFile",
    "SaveSubsError",
    "SubtitleData",
    "SubtitleField",
    "SubtitleFormat",
    "load_file_edit",
    "load_sentence_transformer_model",
    "load_subs",
    "load_subtitles",
    "merge_subtitles",
    "run_merge_pipeline",
    "save_file_combined",
    "save_file_edit",
    "save_file_separate",
    "save_memory_combined",
    "save_memory_edit",
    "save_memory_separate",
    "save_subtitles_in_zip",
]

SubtitleData.__module__ = "duosubs"
SubtitleField.__module__ = "duosubs"

SubtitleFormat.__module__ = "duosubs"
OmitFile.__module__ = "duosubs"
DeviceType.__module__ = "duosubs"
ModelPrecision.__module__ = "duosubs"

LoadModelError.__module__ = "duosubs"
LoadSubsError.__module__ = "duosubs"
MergeSubsError.__module__ = "duosubs"
SaveSubsError.__module__ = "duosubs"
