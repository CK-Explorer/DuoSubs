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

  - `sub_lang_1.srt`
  - `sub_lang_2.ass`

And you want to merge them using the timestamps from `sub_lang_1.srt`.

Here are the **simplest** ways to do it, either way:

  - via command line:

    .. code-block:: bash

        duosubs -p sub_lang_1.srt -s sub_lang_2.ass
        
  - via Python API:

    .. code-block:: python

        from duosubs import MergeArgs, run_merge_pipeline

        # Store all arguments
        args = MergeArgs(
            primary="sub_lang_1.srt",
            secondary="sub_lang_2.ass"
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
    `Qwen/Qwen3-Embedding-4B <https://huggingface.co/Qwen/Qwen3-Embedding-4B>`_, 
    you can run the following command instead:

    .. code-block:: bash

        duosubs -p sub_lang_1.srt -s sub_lang_2.ass --model Qwen/Qwen3-Embedding-4B

It outputs `sub_lang_1.zip` in the **same directory** as `sub_lang_1.srt`, with the 
following structure:

.. code-block:: bash

    sub_lang_1.zip
    ├── sub_lang_1_combined.ass   # Merged subtitles
    ├── sub_lang_1_primary.ass    # Original primary subtitles
    └── sub_lang_1_secondary.ass  # Time-shifted secondary subtitles

All these subtitles are saved in **.ass** format by default.

In the merged file (`sub_lang_1_combined.ass`), the displayed subtitles will have **primary**
subtitles placed **above** the **secondary** subtitles, and **line breaks** are **removed** for 
cleaner formatting.

You can **customize** all these options in :doc:`CLI <cli>` and :doc:`API <api_references>`.
