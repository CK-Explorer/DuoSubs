"""
Pipeline functions for loading, merging, and saving subtitles in the duosubs project.

This module provides the main workflow for subtitle merging, including device selection,
progress logging, error handling, and file output. Used by the CLI and other automation 
scripts.
"""
import platform
from pathlib import Path
from typing import Any, Callable, Optional, Union
from zipfile import ZIP_DEFLATED, ZipFile

import pysubs2
import torch
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from duosubs.common.enums import DeviceType, OmitFile, SubtitleFormat
from duosubs.common.exceptions import (
    LoadModelError,
    LoadSubsError,
    MergeSubsError,
    SaveSubsError,
)
from duosubs.common.types import MergeArgs
from duosubs.core.merger import Merger
from duosubs.io.loader import load_subs
from duosubs.io.writer import (
    save_memory_combined,
    save_memory_edit,
    save_memory_separate,
)
from duosubs.subtitle.data import SubtitleData
from duosubs.subtitle.field import SubtitleField


def run_merge_pipeline(
        args: MergeArgs,
        logger: Optional[Callable[[str], None]] = None
    ) -> None:
    """
    Run the full subtitle merging pipeline: load, merge, and save subtitles.

    Args:
        args (MergeArgs): Arguments for subtitle merging workflow.
        logger (Callable[[str], None], optional): Optional logger for progress messages.
    
    Raises:
        LoadSubsError: If there is an error loading subtitles or if they are empty.
        LoadModelError: If there is an error loading the sentence transformer model.
        MergeSubsError: If there is an error merging subtitles.
        SaveSubsError: If there is an error saving the merged subtitles.
    """
    def make_progress_callback(progress_bar: Any) -> Callable[[float], None]:
        last_percent: list[float] = [0.0]

        def callback(current_percent: float) -> None:
            delta = current_percent - last_percent[0]
            if delta > 0:
                progress_bar.update(delta)
                last_percent[0] = current_percent

        return callback

    (
        log_stage1,
        log_stage2,
        _,
        log_stage4,
        log_stage5
    ) = _progress_logger(logger)
    primary_subs_data, secondary_subs_data = load_subtitles(args, log_stage1)
    model = load_sentence_transformer_model(args, log_stage2)

    if logger:
        with tqdm(
            total=100,
            desc= "Stage 3 -> Merging subtitles",
            bar_format="{l_bar}{bar}| [{elapsed}<{remaining}, {rate_fmt}{postfix}]"
        ) as pbar:
            callback = make_progress_callback(pbar)
            merged_subs = merge_subtitles(
                args,
                model,
                primary_subs_data,
                secondary_subs_data,
                [False],
                progress_callback=callback
            )
    else:
        merged_subs = merge_subtitles(
            args,
            model,
            primary_subs_data,
            secondary_subs_data,
            [False]
        )

    save_subtitles_in_zip(
        args,
        merged_subs,
        primary_subs_data.styles,
        secondary_subs_data.styles,
        log_stage4
    )
    if log_stage5:
        log_stage5()

def load_subtitles(
        args: MergeArgs,
        stage_logger: Optional[Callable[[], None]] = None
    ) -> tuple[SubtitleData, SubtitleData]:
    """
    Load primary and secondary subtitles, styles, and tokens.

    Args:
        args (MergeArgs): Arguments for subtitle merging workflow.
        stage_logger (Callable[[], None], optional): Optional logger for this stage.

    Returns:
        tuple[SubtitleData, SubtitleData]: 
        - Contains primary subtitles, styles, tokens and styles for each token.
        - Contains secondary subtitles, styles, tokens and styles for each token.
    
    Raises:
        LoadSubsError: If there is an error loading subtitles or if they are empty.
    """
    if stage_logger:
        stage_logger()
    try:
        primary_subs_data = load_subs(args.primary)
        secondary_subs_data = load_subs(args.secondary)
    except Exception as e:
        raise LoadSubsError("Error in loading subtitles:", e) from e

    if len(primary_subs_data.subs) == 0:
        raise LoadSubsError(f"Primary subtitle file '{args.primary}' is empty.")

    if len(secondary_subs_data.subs) == 0:
        raise LoadSubsError(f"Secondary subtitle file '{args.secondary}' is empty.")

    return primary_subs_data, secondary_subs_data

def load_sentence_transformer_model(
        args: MergeArgs,
        stage_logger: Optional[Callable[[str, str], None]] = None
    ) -> SentenceTransformer:
    """
    Load a SentenceTransformer model on the specified device.

    Args:
        args (MergeArgs): Arguments for subtitle merging workflow.
        stage_logger (Callable[[str, str], None], optional): Optional logger for this 
            stage.

    Returns:
        SentenceTransformer: Loaded sentence transformer model.
    
    Raises:
        LoadModelError: If there is an error loading the sentence transformer model.
    """
    selected_device = (
        _auto_select_device() if args.device == DeviceType.AUTO
        else args.device.value
    )
    if stage_logger:
        stage_logger(args.model, selected_device)
    try:
        model = SentenceTransformer(
            args.model,
            device=selected_device,
            model_kwargs={
                "torch_dtype": args.model_precision.to_torch_dtype()
            }
        )
    except Exception as e:
        raise LoadModelError(f"Error in loading {args.model}:", e) from e

    return model

def merge_subtitles(
        args: MergeArgs,
        model: SentenceTransformer,
        primary_subs_data: SubtitleData,
        secondary_subs_data: SubtitleData,
        stop_bit: list[bool],
        stage_logger: Optional[Callable[[], None]] = None,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> list[SubtitleField]:
    """
    Merge primary and secondary subtitles using the provided model and configuration.

    Args:
        args (MergeArgs): Arguments for subtitle merging workflow.
        model (SentenceTransformer): Loaded sentence transformer model.
        primary_subs_data (SubtitleData): Primary subtitles data, containing subtitles, 
            styles, tokens, and styles for each token.
        secondary_subs_data (SubtitleData): Secondary subtitles data, containing 
            subtitles, styles, tokens, and styles for each token.
        stop_bit (list[bool]): Flag to stop the merging process early.
        stage_logger (Callable[[], None], optional): Optional logger for this stage.
        progress_callback (Callable[[int], None], optional): Optional callback for 
            progress updates.

    Returns:
        list[SubtitleField]: List of merged subtitle fields.

    Raises:
        MergeSubsError: If there is an error merging subtitles.
    """
    if stage_logger:
        stage_logger()
    try:
        merger = Merger(primary_subs_data, secondary_subs_data)
        merged_subs = merger.merge_subtitle(
            model,
            stop_bit,
            args.ignore_non_overlap_filter,
            args.batch_size,
            progress_callback=progress_callback
        )
    except Exception as e:
        raise MergeSubsError("Error in merging subtitles:", e) from e

    return merged_subs

def save_subtitles_in_zip(
        args: MergeArgs,
        subs: list[SubtitleField],
        primary_styles: pysubs2.SSAFile,
        secondary_styles: pysubs2.SSAFile,
        stage_logger: Optional[Callable[[str], None]] = None
    ) -> None:
    """
    Save merged subtitles with their styles in a zip archive.

    Args:
        args (MergeArgs): Arguments for subtitle merging workflow.
        subs (list[SubtitleField]): List of merged subtitle fields.
        primary_styles (pysubs2.SSAFile): Primary subtitle styles.
        secondary_styles (pysubs2.SSAFile): Secondary subtitle styles.
        stage_logger (Callable[[str], None], optional): Optional logger for this stage.
    
    Raises:
        SaveSubsError: If there is an error saving the merged subtitles.
    """
    def resolve_format(
            specific: Optional[SubtitleFormat],
            fallback: Optional[SubtitleFormat]
        ) -> SubtitleFormat:
        result = specific or fallback
        if result is None:
            result = SubtitleFormat.ASS
        return result

    combined_fmt = resolve_format(args.format_combined, args.format_all)
    primary_fmt = resolve_format(args.format_primary, args.format_all)
    secondary_fmt = resolve_format(args.format_secondary, args.format_all)
    fmt = [f.value for f in (combined_fmt, primary_fmt, secondary_fmt)]

    retained_file_tuple = _retain_files(args.omit)

    primary_path = Path(args.primary)
    output_name = args.output_name or primary_path.stem
    output_dir = args.output_dir or primary_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    if stage_logger:
        stage_logger(output_name)
    try:
        _save_file(
            subs,
            primary_styles,
            secondary_styles,
            output_name,
            output_dir,
            retained_file_tuple,
            fmt,
            args.secondary_above,
            args.retain_newline
        )
    except Exception as e:
        raise SaveSubsError("Error in saving subtitle:", e) from e

def _save_file(
        subs: list[SubtitleField],
        primary_styles: pysubs2.SSAFile,
        secondary_styles: pysubs2.SSAFile,
        output_name: str,
        output_dir: Union[Path, str],
        retained_file_tuple: list[bool],
        subs_fmt: list[str],
        secondary_above: bool,
        retain_newline: bool
    ) -> None:
    """
    Write subtitle files and metadata to a zip archive in the output directory.

    Args:
        subs (list[SubtitleField]): List of merged subtitle fields.
        primary_styles (pysubs2.SSAFile): Primary subtitle styles.
        secondary_styles (pysubs2.SSAFile): Secondary subtitle styles.
        output_name (str): Base name for output files.
        output_dir (Path | str): Output directory for the zip archive.
        retained_file_tuple (list[bool]): Which files to include in the archive.
        subs_fmt (list[str]): File formats for combined, primary, and secondary 
            subtitles.
        secondary_above (bool): Whether secondary subtitle is above primary.
        retain_newline (bool): Whether to retain "\\N" line breaks.
    """
    combined_str = save_memory_combined(
        subs,
        primary_styles,
        secondary_styles,
        subs_fmt[0],
        secondary_above,
        retain_newline
    )
    primary_str, secondary_str = save_memory_separate(
        subs,
        primary_styles,
        secondary_styles,
        subs_fmt[1],
        subs_fmt[2],
        retain_newline
    )
    compressed_bytes = save_memory_edit(subs, primary_styles, secondary_styles)
    zip_path = Path(output_dir) / f"{output_name}.zip"

    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zipf:
        if retained_file_tuple[0]:
            file_name = output_name + "_combined." + subs_fmt[0]
            zipf.writestr(file_name, combined_str)

        if retained_file_tuple[1]:
            file_name = output_name + "_primary." + subs_fmt[1]
            zipf.writestr(file_name, primary_str)

        if retained_file_tuple[2]:
            file_name = output_name + "_secondary." + subs_fmt[2]
            zipf.writestr(file_name, secondary_str)

        if retained_file_tuple[3]:
            file_name = output_name + ".json.gz"
            zipf.writestr(file_name, compressed_bytes)

def _retain_files(omit_list: list[OmitFile]) -> list[bool]:
    """
    Determine which output files to retain based on the omit list.

    Args:
        omit_list (list[OmitFile]): List of file types to omit from output.

    Returns:
        list[bool]: List of booleans indicating which files to retain.
    """
    retained_file_tuple = [False, False, False, False]
    if OmitFile.NONE not in omit_list:
        if OmitFile.COMBINED not in omit_list:
            retained_file_tuple[0] = True
        if OmitFile.PRIMARY not in omit_list:
            retained_file_tuple[1] = True
        if OmitFile.SECONDARY not in omit_list:
            retained_file_tuple[2] = True
        if OmitFile.EDIT not in omit_list:
            retained_file_tuple[3] = True
    else:
        retained_file_tuple = [True, True, True, True]
    return retained_file_tuple

def _auto_select_device() -> str:
    """
    Automatically select the best available device for model inference.

    Returns:
        str: Device string ("cuda", "mps", or "cpu").
    """
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available() and platform.system() == "Darwin":
        return "mps"
    else:
        return "cpu"

def _progress_logger(
    logger: Optional[Callable[[str], None]]
    ) -> tuple[
        Optional[Callable[[], None]],
        Optional[Callable[[str, str], None]],
        Optional[Callable[[], None]],
        Optional[Callable[[str], None]],
        Optional[Callable[[], None]]
    ]:
    """
    Create logger functions for each pipeline stage.

    Args:
        logger (Callable[[str], None], optional): Logger function to use for progress 
            messages.

    Returns:
        tuple: Logger functions for each pipeline stage.
    """
    if logger is None:
        return (None, None, None, None, None)

    def stage_1_logger() -> None:
        logger("Stage 1 -> Loading subtitles")

    def stage_2_logger(model_name: str, device: str) -> None:
        logger(f"Stage 2 -> Loading {model_name} into {device}")

    def stage_3_logger() -> None:
        logger("Stage 3 -> Merging subtitles")

    def stage_4_logger(output_name: str) -> None:
        logger(f"Stage 4 -> Saving files to {output_name}.zip")

    def stage_5_logger() -> None:
        logger("Status  -> Subtitles merged and saved successfully.")

    return (
        stage_1_logger,
        stage_2_logger,
        stage_3_logger,
        stage_4_logger,
        stage_5_logger
    )
