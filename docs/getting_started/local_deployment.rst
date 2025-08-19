Local Deployment
=================

Requirements
-------------

Python versions: |version|

.. |version| image:: https://img.shields.io/pypi/pyversions/duosubs.svg
    :alt: Python Versions

Installation
-------------

1.  Install the correct version of PyTorch by following the official instructions: https://pytorch.org/get-started/locally
2.  Install ``DuoSubs`` via pip:

    .. code-block:: bash

        pip install duosubs

Basic Usage
------------

Let's say you have two subtitle files, from the **same cut** and all their **timestamps overlap** 
(see :ref:`Merging Modes <merging_mode>` for other subtitle file types) — 
in any supported format like `SRT`, `VTT`, `MPL2`, `TTML`, `ASS`, `SSA` — for example:

  - `primary_sub.srt`
  - `secondary_sub.srt`

And you want to merge them using the timestamps from `primary_sub.srt`.

Then, you can do it by:

  - using an :ref:`interactive Web UI <launch-web-ui>`
  - :ref:`merging subtitles directly <merge-direct-cli>`

— whichever suits your workflow. Both methods can be run from the **command line** or 
via **Python code**.

.. _launch-web-ui:

Launching Web UI 
^^^^^^^^^^^^^^^^

.. tab:: Command Line

    .. code-block:: bash

        duosubs launch-webui

.. tab:: Python API

    .. code-block:: python

        from duosubs import create_duosubs_gr_blocks

        # Build the Web UI layout (Gradio Blocks)
        webui = create_duosubs_gr_blocks() 

        # These commands work just like launching a regular Gradio app
        webui.queue(default_concurrency_limit=None) # Allow unlimited concurrent requests
        webui.launch(inbrowser=True)                # Start the Web UI and open it in a browser tab

This will start a local server and display a URL (e.g., http://127.0.0.1:7860), and the Web UI
will be started in a new browser tab.

.. tip::

    You can also launch the server on a different host address (e.g. 0.0.0.0) and port (e.g 8000):

    .. tab:: Command Line

        .. code-block:: bash

            duosubs launch-webui --host 0.0.0.0 --port 8000

    .. tab:: Python API

        .. code-block:: python

            from duosubs import create_duosubs_gr_blocks

            webui = create_duosubs_gr_blocks() 

            webui.queue(default_concurrency_limit=None)
            webui.launch(
                server_name = "0.0.0.0",    # use different address
                server_port = 8000,         # use different port number
                inbrowser=True
            )

.. warning::

    -   The Web UI caches files during processing, and clears files older than 4 hours every 1 hour. 
        Cached data may remain if the server stops unexpectedly, and you may need to delete them 
        manually.
    -   Sometimes, older model may fail to be released after switching or closing sessions. 
        If you run out of RAM or VRAM, simply restart the script.

.. _merge-direct-cli:

Merging Subtitles Directly
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. tab:: Command Line

    .. code-block:: bash

        duosubs merge -p primary_sub.srt -s secondary_sub.srt
        
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

Default Options and Outputs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This tool uses `LaBSE <https://huggingface.co/sentence-transformers/LaBSE>`_ 
as its default Sentence Transformer model and runs on **GPU** or **MPS** (Apple) if available — 
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

            duosubs merge -p primary_sub.srt -s secondary_sub.srt --model Qwen/Qwen3-Embedding-0.6B

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

    .. tab:: Web UI

        .. raw:: html
            
            <div class="code-like">In <code class="docutils literal notranslate"><span class="pre">Configurations</span></code> → <code class="docutils literal notranslate"><span class="pre">Model & Device</span></code> → <code class="docutils literal notranslate"><span class="pre">Sentence Transformer Model</span></code>, replace <code class="docutils literal notranslate"><span class="pre">sentence-transformers/LaBSE</span></code> with <code class="docutils literal notranslate"><span class="pre">Qwen/Qwen3-Embedding-0.6B</span></code>.</div>

    .. warning::

        -   Some models may require significant RAM or GPU (VRAM) to run and might not
            be compatible with all devices — especially larger models. 
        -   Please ensure the selected model supports your desired language for reliable 
            results.

After merging, you'll get `primary_sub.zip` in the **Output Zip** section **(Web UI)**
or in the **same directory** as `primary_sub.srt` **(CLI/Python)**, with the 
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

You can **customize** all these options in the configurations section of the Web UI, 
:doc:`CLI </cli_usage/merge>` or :doc:`Python API </api_references/core_subtitle_merging>`.

.. _merging_mode:

Merging Modes
^^^^^^^^^^^^^^

This tool supports three merging modes:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Mode
     - Same cut
     - Timestamps overlap
   * - ``synced``
     - ✓
     - ✓ (all timestamps)
   * - ``mixed``
     - ✓
     - ✗ (some or all may not overlap)
   * - ``cuts``
     - ✗ (primary being longer version)
     - ✗

To merge with a specific mode (e.g. ``cuts``), run:

.. tab:: Command Line
    
    .. code-block:: bash

        duosubs merge -p primary_sub.srt -s secondary_sub.srt --mode cuts

.. tab:: Python API

    .. code-block:: python

        from duosubs import MergeArgs, MergingMode, run_merge_pipeline

        # Store all arguments
        args = MergeArgs(
            primary="primary_sub.srt",
            secondary="secondary_sub.srt",
            merging_mode=MergingMode.CUTS
        )

        # Load, merge, and save subtitles.
        run_merge_pipeline(args, print)

.. tab:: Web UI

    .. raw:: html
        
        <div class="code-like">In <code class="docutils literal notranslate"><span class="pre">Configurations</span></code> → <code class="docutils literal notranslate"><span class="pre">Alignment Behavior</span></code> → <code class="docutils literal notranslate"><span class="pre">Merging Mode</span></code>, choose <code class="docutils literal notranslate"><span class="pre">Cuts</span></code>.</div>

.. tip::

    Here are some of the simple guidelines to choose the appropriate mode:

    - If both subtitle files are **timestamp-synced**, use ``synced`` for the cleanest result.
    - If timestamps **drift** or only **partially overlap**, use ``mixed``.
    - If subtitles come from **different editions** of the video, with **primary** subtitles being the **extended** or **longer version**, use ``cuts``.
    
    .. note::

        For ``mixed`` and ``cuts`` modes, try to use subtitle files **without scene annotations** 
        if possible, as they may reduce alignment quality.
