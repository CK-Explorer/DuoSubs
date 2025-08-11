"""
Defines the main Gradio UI layout and configuration for DuoSubs subtitle merging web 
app.

This module sets up the UI components, event handlers, and manages the model loading
and merging process. It includes device selection, model configuration, and subtitle 
file handling.
"""


import gradio as gr
import torch

from duosubs.webui.manager.model_manager import ModelPool
from duosubs.webui.monitor import live_memory_monitor

from .common import auto_filter_device, auto_list_gpu_name, open_html
from .constants import (
    DEFAULT_MODEL,
    DEFAULT_PRECISION,
    DEFAULT_SUB_EXT,
    LEADERBOARD_URL,
    PRECISION_LIST,
    SENTENCE_TRANSFORMER_URL,
    SUB_EXT_LIST,
    SUB_EXT_LIST_WITH_DOT,
    TITLE_HTML,
)
from .events import (
    cancel_merging,
    start_merging,
    states_after_merging,
    states_during_merging,
    toggle_gpu_dropdown,
    validate_excluded_subtitle_file,
)

model_pool = ModelPool()
device_list = auto_filter_device()
gpu_list = auto_list_gpu_name()

def create_main_gr_blocks_ui(
        cache_delete_frequency: int = 3600,
        cache_delete_age: int = 14400
    ) -> gr.Blocks:
    """
    Builds and returns the main Gradio Blocks UI for DuoSubs.

    Args:
        cache_delete_frequency (int): How often to delete cache (seconds).
        cache_delete_age (int): Age threshold for cache deletion (seconds).

    Returns:
        gradio.Blocks: The constructed Gradio UI.
    """
    main_block = gr.Blocks(
        title="DuoSubs",
        theme=gr.themes.Ocean(),
        delete_cache=(cache_delete_frequency, cache_delete_age),
        analytics_enabled=False
    )
    ui: gr.Blocks
    with main_block as ui:
        global device_list
        global gpu_list
        global model_pool

        loaded_model_name = gr.State([""])
        loaded_model_device = gr.State([""])
        cancel_state = gr.State([False])
        gpu_list_state = gr.State(gpu_list)

        title_content = open_html(TITLE_HTML)
        gr.HTML(title_content)
        with gr.Row():
            with gr.Column(scale=9):
                (
                    primary_file,
                    secondary_file,
                    merged_file,
                    merge_button,
                    cancel_button
                ) = _create_subtitles_io_block()
            with gr.Column(scale=11):
                with gr.Accordion(
                    label="📊 Live Memory Monitor",
                    open=False
                ):
                    memory_table = gr.Dataframe(
                        headers=["Type", "Usage", "Used", "Total"],
                        interactive=False
                    )
                with gr.Accordion(label="⚙️ Basic Configurations"):
                    with gr.Tab("Model & Device"):
                        (
                            model_name,
                            device_type,
                            device_index,
                            batch_size,
                            model_precision
                        ) =  _create_model_configurations_block(
                            device_list,
                            gpu_list
                        )
                    with gr.Tab("Output Styling"):
                        (
                            retain_newline,
                            secondary_above_primary
                        ) = _create_output_styling_block()
                    with gr.Tab("File Exports"):
                        (
                            omit_subtitles,
                            combined_format,
                            primary_format,
                            secondary_format
                        ) = _create_file_exports_block()
                with gr.Accordion("🛠️ Advanced Configurations", open=False):
                    with gr.Tab("Alignment Behavior"):
                        ignore_non_overlap = _create_alignment_behaviour_block()

        ui.load(fn=live_memory_monitor.auto_refresh, outputs=memory_table)

        device_type.change(
            fn=toggle_gpu_dropdown,
            inputs=device_type,
            outputs=device_index
        )

        omit_subtitles.change(
            fn=validate_excluded_subtitle_file,
            inputs=omit_subtitles
        )
        
        merge_button.click(
            fn=states_during_merging,
            inputs=cancel_state,
            outputs=[merge_button, cancel_button]
        ).then(
            fn=_wrapped_start_merging,
            inputs=[
                primary_file,
                secondary_file,
                model_name,
                device_type,
                device_index,
                batch_size,
                model_precision,
                ignore_non_overlap, 
                retain_newline,
                secondary_above_primary,
                omit_subtitles,
                combined_format, 
                primary_format,
                secondary_format,
                gpu_list_state,
                loaded_model_name,
                loaded_model_device,
                cancel_state
            ],
            outputs=merged_file
        ).then(
            fn=states_after_merging,
            inputs=cancel_state,
            outputs=[merge_button, cancel_button]
        )

        cancel_button.click(
            fn=cancel_merging,
            inputs=cancel_state,
            outputs=cancel_button,
            concurrency_limit=None
        )

        ui.unload(_wrapped_unload_model)
        
    return ui
    
def _create_subtitles_io_block(
    ) -> tuple[gr.File, gr.File, gr.File, gr.Button, gr.Button]:
    """
    Creates subtitle file input/output UI components.

    This function sets up the UI for uploading primary and secondary subtitle files,
    buttons to initiate and cancel the merging process, and creates the merged output 
    file.

    Returns:
        tuple[gradio.File, gradio.File, gradio.File, gradio.Button, gradio.Button]:
        - primary_file
        - secondary_file
        - merged_file
        - merge_button
        - cancel_button
    """
    gr.Markdown("### 📄 Input Subtitles")
    with gr.Row():
        primary_file = gr.File(
            label="Primary Subtitle File",
            file_types=SUB_EXT_LIST_WITH_DOT
        )
        secondary_file = gr.File(
            label="Secondary Subtitle File",
            file_types=SUB_EXT_LIST_WITH_DOT
        )

    gr.Markdown("### 📦 Output Zip")
    merged_file = gr.File(label="Processed Subtitles (in zip)")

    with gr.Row():
        merge_button = gr.Button("Merge")
        cancel_button = gr.Button("Cancel", interactive=False)
    
    return primary_file, secondary_file, merged_file, merge_button, cancel_button

def _create_model_configurations_block(
        device_list: list[str],
        gpu_list: list[str]
    ) -> tuple[gr.Textbox, gr.Radio, gr.Dropdown, gr.Slider, gr.Dropdown]:
    """
    Creates model and device configuration UI components.

    This function sets up the UI for selecting the model name, device type,
    GPU index, batch size, and model precision.

    Args:
        device_list (list[str]): List of available device types.
        gpu_list (list[str]): List of available GPU names.

    Returns:
        tuple[gradio.Textbox, gradio.Radio, gradio.Dropdown, gradio.Slider, 
            gradio.Dropdown]:
        - model_name
        - device_type
        - device_index
        - batch_size
        - model_precision
    """
    with gr.Column():
        model_name = gr.Textbox(
            lines=1,
            label="Sentence Transformer Model",
            value=DEFAULT_MODEL,
            info=(
                f"💡 Pick one from "
                f"[🤗 Hugging Face]({SENTENCE_TRANSFORMER_URL}) "
                f"or check out from the [leaderboard]({LEADERBOARD_URL})"
            )
        )

    hide_gpu_index = True if torch.cuda.is_available() else False
    with gr.Row():
        device_type = gr.Radio(
            label="Device Type",
            choices=device_list,
            value=device_list[0],
            info="Device type to run the model"
        )
        device_index = gr.Dropdown(
            choices=gpu_list,
            label="Available GPU",
            value=gpu_list[0],
            type="index",
            visible=hide_gpu_index,
            info="💡 Only valid when selecting CUDA"
        )

    with gr.Row():
        batch_size = gr.Slider(
            label="Batch Size",
            minimum=8,
            maximum=256,
            value=256,
            step=1,
            info="Number of sentences to process in parallel"
        )
        model_precision = gr.Dropdown(
            choices=PRECISION_LIST,
            label="Model Precision",
            value=DEFAULT_PRECISION,
            info="Precision mode for inference"
        )
    return model_name, device_type, device_index, batch_size, model_precision

def _create_alignment_behaviour_block() -> gr.Checkbox:
    """
    Creates alignment behavior UI components.

    This function sets up a checkbox for ignoring non-overlapping subtitles, in the 
    merging process.

    Returns:
        gradio.Checkbox: Checkbox for alignment behavior.
    """
    with gr.Column():
        ignore_non_overlap = gr.Checkbox(
            label="Ignore Non-Overlap Filter",
            value=False,
            info=(
                "💡 Use only if both subtitles are **semantically identical** "
                "and contain **no added scenes or annotations**"
            )
        )
    return ignore_non_overlap

def _create_output_styling_block() -> tuple[gr.Checkbox, gr.Checkbox]:
    """
    Creates output styling UI components.

    This function sets up checkboxes for retaining newlines in the original subtitles 
    and placing secondary subtitles above primary subtitles in the merged output.

    Returns:
        tuple[gradio.Checkbox, gradio.Checkbox]:
        - retain_newline
        - secondary_above_primary
    """
    with gr.Column():
        retain_newline = gr.Checkbox(
            label="Retain Newlines",
            value=False,
            info="**Retain line breaks** from the original subtitles"
        )
        secondary_above_primary = gr.Checkbox(
            label="Secondary subtitle above primary subtitle",
            value=False,
            info="Place **secondary** subtitle **above** the **primary**"
        )
    
    return retain_newline, secondary_above_primary

def _create_file_exports_block(
    ) -> tuple[gr.CheckboxGroup, gr.Dropdown, gr.Dropdown, gr.Dropdown]:
    """
    Creates file export UI components.

    This function sets up checkboxes for excluding certain subtitle files from the ZIP 
    output, and dropdowns for selecting the format of combined, primary, and secondary 
    subtitles.

    Returns:
        tuple[gradio.CheckboxGroup, gradio.Dropdown, gradio.Dropdown, gradio.Dropdown]:
        - omit_subtitles
        - combined_format
        - primary_format
        - secondary_format
    """
    with gr.Column():
        omit_subtitles = gr.CheckboxGroup(
            ["Combined", "Primary", "Secondary"],
            type="value",
            label="Excluded Subtitle Files from ZIP"
        )
    with gr.Column():
        gr.Markdown("Subtitle Format")
        combined_format = gr.Dropdown(
            choices=SUB_EXT_LIST,
            value=DEFAULT_SUB_EXT,
            label="Combined"
        )
        primary_format = gr.Dropdown(
            choices=SUB_EXT_LIST,
            value=DEFAULT_SUB_EXT,
            label="Primary"
        )
        secondary_format = gr.Dropdown(
            choices=SUB_EXT_LIST,
            value=DEFAULT_SUB_EXT,
            label="Secondary"
        )
    return omit_subtitles, combined_format, primary_format, secondary_format

def _wrapped_unload_model(request: gr.Request) -> None:
    """
    Wrapper for unloading the model for a session.

    Args:
        request (gradio.Request): Gradio request object containing session_hash.
    """
    return model_pool.unload_model(request.session_hash)

def _wrapped_start_merging(
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
        primary_format: str,
        secondary_format: str,
        gpu_list: list[str],
        loaded_model_device: list[str],
        loaded_model_name: list[str],
        cancel_state: list[bool],
        request: gr.Request,
        progress: gr.Progress | None = None
    ) -> str | None:
    """
    Wrapper for starting the merging process with all required arguments.

    Args:
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
    """
    return start_merging(
        model_pool,
        primary_subtitles, secondary_subtitles,
        model_name, device_type, device_index, batch_size, model_precision,
        ignore_non_overlap, retain_newline, secondary_above_primary,
        omit_subtitles, combined_format, primary_format, secondary_format,
        gpu_list,
        loaded_model_device, loaded_model_name, cancel_state,
        request, progress
    )