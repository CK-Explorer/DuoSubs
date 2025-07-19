"""
Type definitions for argument handling in subtitle merging.

This module defines the MergeArgs dataclass, which is used to store and pass all 
arguments for the subtitle merging process. It simplifies function signatures and 
ensures type safety when passing configuration between CLI, loading, merging, and 
saving routines.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union

from .enums import DeviceType, ModelPrecision, OmitFile, SubtitleFormat


@dataclass
class MergeArgs:
    """
    Container for all arguments used in the subtitle merging workflow.

    Attributes:
        primary (Path | str): Path to the primary language subtitle file. Defaults to 
            "" (empty Path).
        secondary (Path | str): Path to the secondary language subtitle file. Defaults 
            to "" (empty Path).
        model (str): Name of the SentenceTransformer model to use. Defaults to "LaBSE".
        device (DeviceType): Device type for model inference (i.e., 'cpu', 'cuda', 
            'mps', 'auto'). Defaults to "DeviceType.AUTO".
        batch_size (int): Batch size for model inference. Defaults to 32.
        model_precision (ModelPrecision): Precision modes for model inference. Defaults 
            to ModelPrecision.FLOAT32.
        ignore_non_overlap_filter (bool): Whether to ignore non-overlapping subtitles 
            filter. Defaults to False.
        retain_newline (bool): Whether to retain '\\N' line breaks in output. Defaults 
            to True.
        secondary_above (bool): Whether to show secondary subtitle above primary. 
            Defaults to True.
        omit (List[OmitFile]): List of file types to omit from output. Defults to 
            List[OmitFile.EDIT]
        format_all (Optional[SubtitleFormat]): File format for all subtitle outputs. 
            Defaults to None.
        format_combined (Optional[SubtitleFormat]): File format for combined subtitle 
            output. Defaults to None.
        format_primary (Optional[SubtitleFormat]): File format for primary subtitle 
            output. Defaults to None.
        format_secondary (Optional[SubtitleFormat]): File format for secondary subtitle 
            output. Defaults to None.
        output_name (Optional[str]): Base name for output files (without extension). 
            Defaults to None.
        output_dir (Optional[Path]): Output directory for generated files. Defaults to 
            None.
    """

    primary: Union[Path, str] = ""
    secondary: Union[Path, str] = ""
    model: str = "LaBSE"
    device: DeviceType = DeviceType.AUTO
    batch_size: int = 32
    model_precision: ModelPrecision = ModelPrecision.FLOAT32
    ignore_non_overlap_filter: bool = False
    retain_newline: bool = False
    secondary_above: bool = False
    omit: List[OmitFile] = field(default_factory=lambda: [OmitFile.EDIT])
    format_all: Optional[SubtitleFormat] = None
    format_combined: Optional[SubtitleFormat] = None
    format_primary: Optional[SubtitleFormat] = None
    format_secondary: Optional[SubtitleFormat] = None
    output_name: Optional[str] = None
    output_dir: Optional[Path]= None
