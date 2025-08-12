Core Subtitle Merging
======================

This section provides examples of how to use the ``DuoSubs`` API for merging subtitles 
programmatically.

High-Level Subtitle Alignment
------------------------------

Here's the most **simplest** way of merging two subtitles using the merging pipeline:

.. code-block:: python

    from duosubs import (DeviceType, MergeArgs, ModelPrecision, OmitFile,
                        SubtitleFormat, run_merge_pipeline)

    # Store all arguments
    args = MergeArgs(
        # Input Files (Required)
        primary="primary_sub.srt",      # primary subtitle file path
        secondary="secondary_sub.srt",  # secondary subtitle file path

        # Model & Inference (Optional)
        model="Qwen/Qwen3-Embedding-0.6B",    # SentenceTransformer model name, default: LaBSE
        device=DeviceType.CPU,      # Device to run the model on: AUTO (default), CPU, CPU, or MPS
        batch_size=128,             # batch size for model inference, any positive integer, default: 32
        model_precision=ModelPrecision.FLOAT16, # precision mode for model inference: FLOAT32 (default), FLOAT16, or BFLOAT16

        # Alignment Behavior (Optional)
        ignore_non_overlap_filter=False,    # whether to ignore non-overlapping subtitles filter: True or False (default)
        
        # Output Styling (Optional)
        retain_newline=False,       # whether to retain "\N" line breaks in output: True (default) or False
        secondary_above=False,      # whether to show secondary subtitle above primary: True (default) or False

        # Output Files (Optional)
        omit=[
            # OmitFile.EDIT,        # omit edit file, if you want to omit it, uncomment this line
            # OmitFile.PRIMARY,     # omit primary file, if you want to omit it, uncomment this line
            # OmitFile.SECONDARY,   # omit secondary file, if you want to omit it, uncomment this line
            # OmitFile.COMBINED,    # omit combined file, if you want to omit it, uncomment this line
            OmitFile.NONE           # do not omit any files, you can remove this line if you want to keep all files
        ],  # Default: [OmitFile.EDIT]

        # The following arguments accept SubtitleFormat enum values: SRT, VTT, MPL, TTML, ASS, SSA
        format_all=SubtitleFormat.VTT,       # file format for all subtitle outputs, default: ASS
        format_combined=None,                # file format for combined subtitle output, default: None
        format_primary=None,                 # file format for primary subtitle output, default: None
        format_secondary=SubtitleFormat.SSA, # file format for secondary subtitle output, default: None

        output_name="processed_sub",         # base name for output files (without extension), default: primary subtitle name
        output_dir=None     # output directory for generated files, default: primary subtitle location
    )

    # Load, merge, and save subtitles, all inside the pipeline
    run_merge_pipeline(args, print)

Just create a :meth:`duosubs.MergeArgs` instance, tweak the settings needed, and pass it to 
:meth:`duosubs.run_merge_pipeline`. It'll generate ``processed_sub.zip`` containing the subtitle 
files based on the specified omit settings.

Modular Pipeline Usage
------------------------

For more **flexibility**, you can use the modular pipeline, i.e.

    - :meth:`duosubs.load_subtitles`
    - :meth:`duosubs.load_sentence_transformer_model`
    - :meth:`duosubs.merge_subtitles`
    - :meth:`duosubs.save_subtitles_in_zip`

The following code lets you to add extra steps like pre- or post-processing of subtitles between 
:meth:`duosubs.merge_subtitles`.

.. code-block:: python

    import logging
    from typing import Any, Callable

    from tqdm import tqdm

    from duosubs import (LoadModelError, LoadSubsError, MergeArgs, MergeSubsError,
                        SaveSubsError, load_sentence_transformer_model,
                        load_subtitles, merge_subtitles, save_subtitles_in_zip)

    # Store all arguments
    args = MergeArgs(
        # Input Files (Required)
        primary="primary_sub.srt",      # primary subtitle file path
        secondary="secondary_sub.srt",  # secondary subtitle file path

        # For other options, please refer to the High-Level Subtitle Alignment.
    )

    def make_progress_callback(progress_bar: Any) -> Callable[[float], None]:
        """ 
        Creates a callback function to update the progress bar statically, instead 
        of incrementally.
        """
        last_percent: list[float] = [0.0]

        def callback(current_percent: float) -> None:
            delta = current_percent - last_percent[0]
            if delta > 0:
                progress_bar.update(delta)
                last_percent[0] = current_percent

        return callback

    try:
        # 1. Load both subtitles
        primary_subs_data, secondary_subs_data = load_subtitles(
            args, 
            lambda: print("Stage 1 -> Loading subtitles") # Status logger
        )

        # 2. Load the Sentence Transformer model for inference
        model = load_sentence_transformer_model(
            args,
            lambda model_name, device:
            print(f"Stage 2 -> Loading {model_name} on {device.upper()}") # Status logger
        )

        # 3. You can prepocess the subtitles here, like further filtering the subtitles.

        # 4. Merge the subtitles
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
                [False],    # stop_bit, can be used to stop the merging process early
                progress_callback=callback # Note: the progress is incrementally updated inside the function.
            )

        # 5. Post processing the merged subtitles can be done here, like changing styles, etc.

        # 6. Save the merged subtitles in a zip file
        save_subtitles_in_zip(
            args,
            merged_subs,
            primary_subs_data.styles,
            secondary_subs_data.styles,
            lambda output_name: 
            print(f"Stage 4 -> Saving files to {output_name}.zip") # Status logger
        )

        print("Status  -> Subtitles merged and saved successfully.")

    except LoadSubsError as e1:
        logging.error(str(e1), exc_info=True)
    except LoadModelError as e2:
        logging.error(str(e2), exc_info=True)
    except MergeSubsError as e3:
        logging.error(str(e3), exc_info=True)
    except SaveSubsError as e4:
        logging.error(str(e4), exc_info=True)

Under-the-Hood Merging API
--------------------------

You can customize the merging process by **using the core algorithm directly** from the class 
:meth:`duosubs.Merger`. 

This allows you to implement your own logic around the merging process.

.. code-block:: python

    from typing import Any, Callable

    from tqdm import tqdm

    from duosubs import (Merger, MergeArgs, 
                        load_sentence_transformer_model,
                        load_subtitles, save_subtitles_in_zip)

    args = MergeArgs(
        primary="primary_sub.srt",
        secondary="secondary_sub.srt"
    )

    primary_subs_data, secondary_subs_data = load_subtitles(
        args, 
        lambda: print("Stage 1 -> Loading subtitles")
    )

    model = load_sentence_transformer_model(
        args,
        lambda model_name, device:
        print(f"Stage 2 -> Loading {model_name} on {device.upper()}")
    )

    def make_progress_callback(progress_bar: Any) -> Callable[[float], None]:
        last_percent: list[float] = [0.0]

        def callback(current_percent: float) -> None:
            delta = current_percent - last_percent[0]
            if delta > 0:
                progress_bar.update(delta)
                last_percent[0] = current_percent

        return callback

    # Merging the subtitles
    merger = Merger(primary_subs_data, secondary_subs_data)
    stop_bit = [False] # You can create a function to stop the following merging process early.

    with tqdm(
        total=100,
        desc= "Stage 3 -> Merging subtitles",
        bar_format="{l_bar}{bar}| [{elapsed}<{remaining}, {rate_fmt}{postfix}]"
    ) as pbar:
        # If you insert any additional steps between the merging process,
        # do not use the progress_callback function.
        progress_callback = make_progress_callback(pbar)

        # 1. Extract and filter non-overlapping subs
        (
            non_overlap_primary_subs,
            non_overlap_secondary_subs 
        ) = merger.extract_non_overlapping_subs(stop_bit, progress_callback)

        # 2. Estimate tokenized subtitle pairings using DTW
        processed_subs = merger.align_subs_with_dtw(
            model,
            stop_bit,
            args.batch_size,
            progress_callback
        )

        # 3. Refine alignment using a sliding window approach
        stage_number = 0
        window_sizes = [3, 2]
        for window_size in window_sizes:
            processed_subs, stage_number = merger.align_subs_using_neighbours(
                processed_subs,
                window_size,
                model,
                stage_number,
                stop_bit,
                args.batch_size,
                progress_callback
            )

        # 4. Combine aligned and non-overlapping subtitles
        processed_subs.extend(non_overlap_primary_subs)
        processed_subs.extend(non_overlap_secondary_subs)
        processed_subs.sort()

        # 5. Clean up unnecessary newlines in subtitle text fields.
        processed_subs = merger.eliminate_unnecessary_newline(
            processed_subs,
            stop_bit,
            progress_callback
        )

    # The 5 merging steps above are encapsulated in the following high-level function.
    # To use the simplified version, comment out the steps above and uncomment the line below:
    #    processed_subs = merger.merge_subtitle(
    #        model,
    #        stop_bit,
    #        args.ignore_non_overlap_filter,
    #        args.batch_size,
    #        progress_callback
    #    )

    save_subtitles_in_zip(
        args,
        processed_subs,
        primary_subs_data.styles,
        secondary_subs_data.styles,
        lambda output_name: 
        print(f"Stage 4 -> Saving files to {output_name}.zip")
    )

    print("Status  -> Subtitles merged and saved successfully.")

Low-Level Subtitle I/O API
---------------------------

Subtitle File Loading Utilities
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you only need to **load a single subtitle file**, use :meth:`duosubs.load_subs` instead of 
:meth:`duosubs.load_subtitles`.

It returns a :meth:`duosubs.SubtitleData` instance that includes:

    - list of :meth:`duosubs.SubtitleField`
    - style information
    - list of tokenized sentences
    - list of style-level tokens

.. code-block:: python

    from duosubs import load_subs

    subs_data = load_subs("primary_sub.srt")

To **load an edit file** (with a ``.json.gz`` extension) generated by this tool for 
**internal use**, use the :meth:`duosubs.load_file_edit` function.

It returns list of :meth:`duosubs.SubtitleField` along with both primary and secondary style 
information.

.. code-block:: python

    from duosubs import load_file_edit

    subs_data = load_file_edit("sub_edit.json.gz")

Subtitle File Writing Utilities
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you prefer to **save** the files **separately** instead of as a single ZIP archive, 
you can use the following approach.

There are two ways of saving the subtitle files:

  - to **disk**

    - :meth:`duosubs.save_file_combined`
    - :meth:`duosubs.save_file_separate`
    - :meth:`duosubs.save_file_edit`

  - to **memory** — useful for in-memory processing (e.g. compression or packaging)

    - :meth:`duosubs.save_memory_combined`
    - :meth:`duosubs.save_memory_separate`
    - :meth:`duosubs.save_memory_edit`

Below is an example of **saving** subtitles to **disk**. Each function can also be 
**used independently**:

.. code-block:: python

    from pathlib import Path

    import pysubs2

    from duosubs import (SubtitleField, save_file_combined, save_file_edit,
                        save_file_separate)

    merged_subs = [
        SubtitleField(
            start=0,
            end=1000,
            primary_text="Hello!",
            secondary_text="Bonjour!"
        )
    ]   # Assume this is a list containing subtitle fields after merging process
    primary_styles = pysubs2.SSAFile()      # Suppose this contains the primary style
    secondary_styles = pysubs2.SSAFile()    # Suppose this contains the secondary style

    path = Path("D:/Users/Name/Documents/Folder")

    # Saves both merged subtitles into a single file
    save_file_combined(
        merged_subs,
        primary_styles,
        secondary_styles,
        save_path = path / "sub_combined.ass",
        secondary_above = False,
        retain_newline = False
    )

    # Saves the primary and secondary subtitle files separately
    save_file_separate(
        merged_subs,
        primary_styles,
        secondary_styles,
        save_path_primary = path / "sub_primary.ass",
        save_path_secondary = path / "sub_secondary.ass",
        retain_newline=False
    )

    # Saves the list of SubtitleFields along with primary and secondary style information to a compressed file.
    # Intended for internal use only.
    save_file_edit(
        merged_subs,
        primary_styles,
        secondary_styles,
        save_path = path / "sub_edit.json"
    )

Alternatively, you can **save** the merged subtitles to **memory** for further processing. 
Similarly, each function **supports separate usage**:

.. code-block:: python

    import pysubs2

    from duosubs import (SubtitleField, save_memory_combined, save_memory_edit,
                        save_memory_separate)

    merged_subs = [
        SubtitleField(
            start=0,
            end=1000,
            primary_text="Hello!",
            secondary_text="Bonjour!"
        )
    ]   # Assume this is a list containing subtitle fields after merging process
    primary_styles = pysubs2.SSAFile()      # Suppose this contains the primary style
    secondary_styles = pysubs2.SSAFile()    # Suppose this contains the secondary style

    # Saves both merged subtitles into bytes
    combined_subs_bytes = save_memory_combined(
        merged_subs,
        primary_styles,
        secondary_styles,
        extension_fmt = "srt",
        secondary_above = False,
        retain_newline = False
    )

    # Saves the primary and secondary subtitle into two separate bytes
    primary_subs_bytes, secondary_subs_bytes = save_memory_separate(
        merged_subs,
        primary_styles,
        secondary_styles,
        extension_primary = "ass",
        extension_secondary = "ass",
        retain_newline=False
    )

    # Saves the list of SubtitleFields along with primary and secondary style information to a compressed bytes.
    # Intended for internal use only.
    edit_subs_bytes = save_memory_edit(
        merged_subs,
        primary_styles,
        secondary_styles
    )
