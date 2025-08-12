
"""
Event handlers and UI logic for subtitle merging, model management, and device selection
in DuoSubs web UI.

This module contains functions to handle merging of subtitles, manage model loading and 
unloading, and update UI elements based on user interactions. It integrates with the 
ModelPool for efficient model management.
"""

from pathlib import Path
from typing import Any

import gradio as gr
from sentence_transformers import SentenceTransformer

from duosubs.common.enums import DeviceType, ModelPrecision, OmitFile, SubtitleFormat
from duosubs.common.exceptions import (
                                  LoadModelError,
                                  LoadSubsError,
                                  MergeSubsError,
                                  SaveSubsError,
)
from duosubs.common.types import MergeArgs
from duosubs.core.merge_pipeline import (
    load_subtitles,
    merge_subtitles,
    save_subtitles_in_zip,
)
from duosubs.webui.manager.model_manager import ModelPool


def start_merging(
        model_pool: ModelPool,
        primary_subtitles: str,
        secondary_subtitles: str,
        model_name: str,
        device_type: str,
        device_index: int,
        batch_size: int,
        model_precision: str,
        ignore_non_overlap: bool,
        retain_newline: bool,
        secondary_above_primary: bool,
        omit_subtitles: list[str],
        combined_format: str,
        primary_format:str,
        secondary_format: str,
        gpu_list: list[str],
        loaded_model_device: list[str],
        loaded_model_name: list[str],
        cancel_state: list[bool],
        request: gr.Request,
        progress: gr.Progress | None = None
    ) -> str | None:
    """
    The main function to handle the merging process of subtitles, which starts from 
    loading subtitles, loading the model, merging subtitles, and saving the output in 
    a ZIP file.

    Args:
        model_pool (ModelPool): ModelPool instance for managing models.
        primary_subtitles (str): Path to primary subtitle file.
        secondary_subtitles (str): Path to secondary subtitle file.
        model_name (str): Name of the model to use.
        device_type (str): Device type (e.g., 'cpu', 'cuda').
        device_index (int): Index of the selected GPU.
        batch_size (int): Batch size for inference.
        model_precision (str): Precision mode for inference.
        ignore_non_overlap (bool): Whether to ignore non-overlapping subtitles.
        retain_newline (bool): Whether to retain newlines in output.
        secondary_above_primary (bool): Whether to place secondary subtitle above 
            primary.
        omit_subtitles (list[str]): List of subtitle types to omit from output.
        combined_format (str): Format for combined subtitles.
        primary_format (str): Format for primary subtitles.
        secondary_format (str): Format for secondary subtitles.
        gpu_list (list[str]): List of available GPU names.
        loaded_model_device (list[str]): List tracking loaded model device.
        loaded_model_name (list[str]): List tracking loaded model name.
        cancel_state (list[bool]): List tracking cancellation state.
        request (gradio.Request): Gradio request object.
        progress (gradio.Progress) : Gradio progress object (optional). 
            Defaults to None.

    Returns:
        str | None: Path to the output ZIP file, or None if cancelled.

    Raises:
        gradio.Error: If any error occurs during loading, merging, or saving subtitles.
    """
    if progress is None:
        progress = gr.Progress()

    args = MergeArgs(
        primary=primary_subtitles,
        secondary=secondary_subtitles,
        model_precision=ModelPrecision(model_precision),
        batch_size=int(batch_size),
        ignore_non_overlap_filter=ignore_non_overlap,
        retain_newline=retain_newline,
        secondary_above=secondary_above_primary,
        omit=[OmitFile.EDIT],
        format_combined=SubtitleFormat(combined_format),
        format_primary=SubtitleFormat(primary_format),
        format_secondary=SubtitleFormat(secondary_format)
    )

    if "Combined" in omit_subtitles:
        args.omit.append(OmitFile.COMBINED)
    if "Primary" in omit_subtitles:
        args.omit.append(OmitFile.PRIMARY)
    if "Secondary" in omit_subtitles:
        args.omit.append(OmitFile.SECONDARY)
    
    zip_name_with_path: str | None = None

    if len(args.omit) == 4:
        gr.Warning(
            (
                "Nothing to merge — Please adjust "
                "<strong><em>Excluded Subtitle Files</em></strong> options "
                "in <strong><em>File Exports</em></strong>"
            ),
            duration=7
        )
        return zip_name_with_path

    try:
        if not cancel_state[0]:
            progress(progress=0, desc= "Stage 1 → Loading subtitles", total=1)
            primary_subs_data, secondary_subs_data = load_subtitles(args)
            progress(progress=1, desc= "Stage 1 → Loading subtitles", total=1)

        device = (
            f"{device_type}:{device_index}" 
            if device_type=="cuda" else device_type
        )
        
        if not cancel_state[0]:
            if (
                loaded_model_name[0] != model_name
                or loaded_model_device[0] != device
            ):
                model_pool.unload_model(request.session_hash)
            
            device_name = (
                gpu_list[device_index] 
                if device_type=="cuda" else device_type.upper()
            )
            progress(
                progress=0,
                desc= (
                    f"Stage 2 → Loading {model_name} on {device_name}"
                ),
                total=1
            )
            model = model_pool.load_model(
                request.session_hash,
                model_name,
                device,
                lambda: SentenceTransformer(
                    model_name,
                    device=device,
                    model_kwargs={
                        "torch_dtype": ModelPrecision(model_precision).to_torch_dtype()
                    }
                )
            )
            loaded_model_name[0] = model_name
            loaded_model_device[0] = device
            progress(
                progress=1,
                desc= (
                    f"Stage 2 → Loading {model_name} on {device_name}"
                ),
                total=1
            )

        if not cancel_state[0]:
            def update_progress(current: int) -> None:
                progress(
                    progress=current/100,
                    desc= f"Stage 3 → Merging subtitles using {model_name}",
                    total=100
                )
            if model is None:
                raise LoadModelError("Model must be loaded before merging.")
            merged_subs = merge_subtitles(
                args,
                model,
                primary_subs_data,
                secondary_subs_data,
                cancel_state,
                progress_callback=update_progress
            )

        if not cancel_state[0]:
            full_zip_path_without_ext = str(Path(args.primary).with_suffix(""))
            zip_name_with_path = f"{full_zip_path_without_ext}.zip"
            zip_name = Path(zip_name_with_path).name
            progress(
                progress=0,
                desc= f"Stage 4 → Compressing files into {zip_name}",
                total=1
            )
            save_subtitles_in_zip(
                args,
                merged_subs,
                primary_subs_data.styles,
                secondary_subs_data.styles
            )
            progress(
                progress=1,
                desc= f"Stage 4 → Compressing files into {zip_name}",
                total=1
            )

        if cancel_state[0]:
            gr.Info("The merging process is stopped.", duration=7)

    except LoadSubsError as e1:
        raise gr.Error(str(e1)) from e1
    except LoadModelError as e2:
        raise gr.Error(str(e2)) from e2
    except MergeSubsError as e3:
        raise gr.Error(str(e3)) from e3
    except SaveSubsError as e4:
        raise gr.Error(str(e4)) from e4

    return zip_name_with_path

def cancel_merging(cancel_state: list[bool]) -> gr.Button:
    """
    Cancels the merging process and updates the UI state.

    Args:
        cancel_state (list[bool]): List tracking cancellation state.

    Returns:
        gradio.Button: Cancel button with updated interactivity.
    """
    cancel_state[0] = True
    gr.Info("Cancelling merge process...", duration=7)
    return gr.Button("Cancel", interactive=False)

def states_during_merging(cancel_state: list[bool]) -> tuple[gr.Button, gr.Button]:
    """
    Sets UI state for buttons during the merging process, which disables the Merge 
    button and enables the Cancel button.

    Args:
        cancel_state (list[bool]): List tracking cancellation state.

    Returns:
        tuple[gradio.Button, gradio.Button]: Updated Merge and Cancel buttons.
    """
    cancel_state[0] = False
    return gr.Button("Merge", interactive=False), gr.Button("Cancel", interactive=True)

def states_after_merging(cancel_state: list[bool]) -> tuple[gr.Button, gr.Button]:
    """
    Sets UI state for buttons after the merging process, which enables the Merge button
    and disables the Cancel button.

    Args:
        cancel_state (list[bool]): List tracking cancellation state.

    Returns:
        tuple[gradio.Button, gradio.Button]: Updated Merge and Cancel buttons.
    """
    cancel_state[0] = False
    return gr.Button("Merge", interactive=True), gr.Button("Cancel", interactive=False)

def toggle_gpu_dropdown(device_option: str) -> dict[str, Any]:
    """
    Toggles the GPU dropdown interactivity based on device selection.

    This function enables the GPU dropdown if CUDA is selected,
    otherwise it disables the dropdown.

    Args:
        device_option: Selected device type.

    Returns:
        dict[str, Any]: Gradio update dictionary for dropdown interactivity.
    """
    if device_option == DeviceType.CUDA.value:
        return gr.update(interactive=True)
    else:
        return gr.update(interactive=False)

def validate_excluded_subtitle_file(selected: list[str]) -> None:
    """
    Validates the selected options for excluded subtitle files.
    If all options are selected, it shows a warning message.

    Args:
        selected (list[str]): List of selected options.
    """
    if len(selected) == 3:
        gr.Warning(
            (
                "Nothing to merge — Please adjust "
                "<strong><em>Excluded Subtitle Files</em></strong> options "
                "in <strong><em>File Exports</em></strong>"
            ),
            duration=7
        )
