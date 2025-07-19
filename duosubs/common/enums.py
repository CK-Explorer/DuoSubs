"""
Enum definitions for subtitle merging CLI options.

This module defines enums for supported subtitle file formats, output file omission 
options, device types and precision modes used for model inference. These enums are 
used throughout the CLI and merging logic to ensure type safety and clear option 
handling.
"""

from enum import Enum

import torch


class SubtitleFormat(str, Enum):
    """
    Enum for supported subtitle file formats.

    Attributes:
        SRT (str): SubRip subtitle format ('.srt').
        VTT (str): WebVTT subtitle format ('.vtt').
        MPL2 (str): MPL2 subtitle format ('.mpl2').
        TTML (str): Timed Text Markup Language format ('.ttml').
        ASS (str): Advanced SubStation Alpha format ('.ass').
        SSA (str): SubStation Alpha format ('.ssa').
    """
    SRT = "srt"
    VTT = "vtt"
    MPL2 = "mpl2"
    TTML = "ttml"
    ASS = "ass"
    SSA = "ssa"

class OmitFile(str, Enum):
    """
    Enum for file types that can be omitted from output packaging.

    Attributes:
        NONE (str): No file is omitted.
        COMBINED (str): Combined subtitle file.
        PRIMARY (str): Primary subtitle file.
        SECONDARY (str): Secondary subtitle file.
        EDIT (str): Edit file (e.g., for project or intermediate data).
    """
    NONE = "none"
    COMBINED = "combined"
    PRIMARY = "primary"
    SECONDARY = "secondary"
    EDIT = "edit"

class DeviceType(str, Enum):
    """
    Enum for device types used to run the model.

    Attributes:
        CPU (str): Use CPU for computation.
        CUDA (str): Use Nvidia or AMD GPU for computation.
        MPS (str): Use Apple Metal Performance Shaders for computation.
        AUTO (str): Automatically select the best available device.
    """
    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"
    AUTO = "auto"

class ModelPrecision(str, Enum):
    """
    Enum options for precision mode used in model inference.

    Attributes:
        FLOAT32 (str): 32-bit floating point (full precision)
        FLOAT16 (str): 16-bit floating point (half precision)
        BFLOAT16 (str): Brain Floating Point 16-bit precision (optimized for newer 
            hardware)
    """
    FLOAT32 = "float32"
    FLOAT16 = "float16"
    BFLOAT16 = "bfloat16"

    def to_torch_dtype(self) -> torch.dtype:
        """
        Converts the precision enum value to a corresponding PyTorch dtype.

        Returns:
            torch.dtype: Corresponding PyTorch dtype for the precision.
        """
        return {
            "float32": torch.float,
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
        }[self.value]
