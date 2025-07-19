"""
CLI entry point for the duosubs subtitle merging tool.

This module provides the Typer-based command-line interface for merging subtitle files 
using semantic alignment.

It supports model/device selection, output formatting, and error handling. See the 
'merge' command for details.
"""

import sys
from pathlib import Path
from typing import List, NoReturn, Optional

import typer

from duosubs.common.constants import SUPPORTED_SUB_EXT
from duosubs.common.enums import DeviceType, ModelPrecision, OmitFile, SubtitleFormat
from duosubs.common.exceptions import (
    LoadModelError,
    LoadSubsError,
    MergeSubsError,
    SaveSubsError,
)
from duosubs.common.types import MergeArgs
from duosubs.core.merge_pipeline import run_merge_pipeline

DEFAULT_SAVED_SUB_EXT: SubtitleFormat = SubtitleFormat.ASS
DEFAULT_OVERLAP_TIME: int = 500 # in ms
DEFAULT_WINDOW_SIZE: int = 5
DEFAULT_BATCH_SIZE: int = 32
DEFAULT_PRECISION: ModelPrecision = ModelPrecision.FLOAT32
DEFAULT_OMIT_FILES_LIST: List[OmitFile] = [OmitFile.EDIT]
DEFAULT_SUPPORTED_SUBS_STR = ", ".join(SUPPORTED_SUB_EXT)

app = typer.Typer(add_completion=True)

# ruff: noqa: B008
@app.command(help=f"""
Merge two subtitle files by aligning them based on semantic meaning.\n
             
Supported format:\n
{DEFAULT_SUPPORTED_SUBS_STR}\n\n

Usage example:\n
duosubs -p en.srt -s es.srt --model LaBSE\n
duosubs -p en.srt -s es.srt --format-all srt --output-dir output/\n
""")
def merge(
    # Input Subtitles
    primary: Path = typer.Option(
        ...,
        "--primary", "-p",
        help="Path to the primary language subtitle file"
    ),
    secondary: Path = typer.Option(
        ...,
        "--secondary", "-s",
        help="Path to the secondary language subtitle file"
    ),

    # Model Settings
    model: str = typer.Option(
        "LaBSE",
        help="Name of the SentenceTransformer model (e.g. LaBSE)"
    ),
    device: DeviceType = typer.Option(
        "auto",
        help="Device to run the model",
        case_sensitive=False
    ),
    batch_size: int = typer.Option(
        DEFAULT_BATCH_SIZE,
        help=(
            "Number of sentences to process in parallel. "
            "Larger values use more memory."
        ),
        min=0
    ),
    model_precision: ModelPrecision = typer.Option(
        DEFAULT_PRECISION,
        help=(
            "Precision mode for inference: float32 (accurate), "
            "float16/bfloat16 (faster, lower memory)."
        ),
        case_sensitive=False
    ),

    # Merge Settings
    ignore_non_overlap_filter: bool = typer.Option(
        False,
        help=(
            "Use only if both subtitles are semantically identical "
            "and contain no added scenes or annotations."
        )
    ),

    # Subtitle Content Options
    retain_newline: bool = typer.Option(
        False,
        help="Retain '\\N' line breaks from the original subtitles"
    ),
    secondary_above: bool = typer.Option(
        False,
        help="Show secondary subtitle above the primary"
    ),

    # Packaging Options
    omit: List[OmitFile] = typer.Option(
        DEFAULT_OMIT_FILES_LIST,
        help="List of files to omit from the output zip",
        case_sensitive=False
    ),
    format_all: Optional[SubtitleFormat] = typer.Option(
        DEFAULT_SAVED_SUB_EXT,
        help="File format for all subtitle outputs",
        case_sensitive=False
    ),
    format_combined: Optional[SubtitleFormat] = typer.Option(
        None,
        help="File format for the combined subtitle (overrides --format-all)",
        case_sensitive=False
    ),
    format_primary: Optional[SubtitleFormat] = typer.Option(
        None,
        help="File format for the primary subtitle (overrides --format-all)",
        case_sensitive=False
    ),
    format_secondary: Optional[SubtitleFormat] = typer.Option(
        None,
        help="File format for the secondary subtitle (overrides --format-all)",
        case_sensitive=False
    ),

    # Output Settings
    output_name: Optional[str] = typer.Option(
        None,
        help=(
            "Base name for output files (without extension). "
            "Defaults to primary subtitle's base name."
        )
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        help="Output directory. Defaults to primary subtitle's location. "
    )
) -> None:
    args = MergeArgs(
        primary=primary,
        secondary=secondary,
        model=model,
        device=device,
        batch_size=batch_size,
        model_precision=model_precision,
        ignore_non_overlap_filter=ignore_non_overlap_filter,
        retain_newline=retain_newline,
        secondary_above=secondary_above,
        omit=omit,
        format_all=format_all,
        format_combined=format_combined,
        format_primary=format_primary,
        format_secondary=format_secondary,
        output_name=output_name,
        output_dir=output_dir
    )
    try:
        run_merge_pipeline(args, typer.echo)
    except LoadSubsError as e1:
        _fail(str(e1), 1)
    except LoadModelError as e2:
        _fail(str(e2), 2)
    except MergeSubsError as e3:
        _fail(str(e3), 3)
    except SaveSubsError as e4:
        _fail(str(e4), 4)

def _fail(msg: str, code_value: int) -> NoReturn:
    """
    Print an error message to stderr and exit with the given code.

    Args:
        msg (str): The error message to print.
        code_value (int): The exit code to use.

    Raises:
        typer.Exit: Always raised to exit the CLI with the given code.
    """
    typer.echo(msg, file=sys.stderr)
    raise typer.Exit(code=code_value)

if __name__ == "__main__":
    app()
