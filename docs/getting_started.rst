Getting Started
===============

Requirements
--------------

- Python **3.10+**

Installation
------------

1.  Install the correct version of PyTorch by following the official instructions: https://pytorch.org/get-started/locally
2.  Install ``DuoSubs`` via pip:

    .. code-block:: bash

        pip install duosubs

Basic Usage
-----------

Let's say you have two subtitle files — in any supported format like `SRT`, `VTT`, 
`MPL2`, `TTML`, `ASS`, `SSA` — for example:

  - `primary_sub.srt`
  - `secondary_sub.srt`

And you want to merge them using the timestamps from `primary_sub.srt`.

Here are the **simplest** ways to do it:

.. tab:: Command Line

    .. code-block:: bash

        duosubs -p primary_sub.srt -s secondary_sub.srt
        
.. tab:: Python API

    .. code-block:: python

        from duosubs import MergeArgs, run_merge_pipeline

        # Store all arguments
        args = MergeArgs(
            primary="primary_sub.srt",
            secondary="secondary_sub.srt"
        )

        # Load, merge, and save subtitles.
        run_merge_pipeline(args, print)

By default, this tool uses `LaBSE <https://huggingface.co/sentence-transformers/LaBSE>`_ 
as its Sentence Transformer model and runs on **GPU** or **MPS** (Apple) if available — 
otherwise it falls back to CPU.

.. tip::

    You can experiment with different models, by choosing one from 
    `🤗 Hugging Face <https://huggingface.co/models?library=sentence-transformers>`_
    or 
    `leaderboard <https://huggingface.co/spaces/mteb/leaderboard>`_.

    For example, if the model chosen is 
    `Qwen/Qwen3-Embedding-0.6B <https://huggingface.co/Qwen/Qwen3-Embedding-0.6B>`_, 
    you can run the followings instead:

    .. tab:: Command Line
    
        .. code-block:: bash

            duosubs -p primary_sub.srt -s secondary_sub.srt --model Qwen/Qwen3-Embedding-0.6B

    .. tab:: Python API

        .. code-block:: python

            from duosubs import MergeArgs, run_merge_pipeline

            # Store all arguments
            args = MergeArgs(
                primary="primary_sub.srt",
                secondary="secondary_sub.srt",
                model="Qwen/Qwen3-Embedding-0.6B"
            )

            # Load, merge, and save subtitles.
            run_merge_pipeline(args, print)

    ⚠️ Note: Some models may require significant RAM or GPU (VRAM) to run, and might 
    not be compatible with all devices — especially larger models.

It outputs `primary_sub.zip` in the **same directory** as `primary_sub.srt`, with the 
following structure:

.. code-block:: bash

    primary_sub.zip
    ├── primary_sub_combined.ass   # Merged subtitles
    ├── primary_sub_primary.ass    # Original primary subtitles
    └── primary_sub_secondary.ass  # Time-shifted secondary subtitles

All these subtitles are saved in **.ass** format by default.

In the merged file (`primary_sub_combined.ass`), the displayed subtitles will have **primary**
subtitles placed **above** the **secondary** subtitles, and **line breaks** are **removed** for 
cleaner formatting.

You can **customize** all these options in :doc:`CLI <cli>` and :doc:`API <api_references>`.
