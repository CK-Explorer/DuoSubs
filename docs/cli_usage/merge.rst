Merge Command
==============

The ``merge`` command merges two subtitle files by aligning them based on semantic meaning.

Required Options
----------------

These are the **minimum required options** to successfully run the ``merge`` command:

Input Files
^^^^^^^^^^^^

-   | ``-p``, ``--primary <file>``  
    | Path to the **primary** subtitle file.

-   | ``-s``, ``--secondary <file>``  
    | Path to the **secondary** subtitle file.

*Example*:

.. code-block:: bash

    duosubs merge -p primary_sub.srt -s secondary_sub.srt

Optional Options
-----------------

Feel free to adjust these options based on your preferences.

Model & Inference
^^^^^^^^^^^^^^^^^^

-   | ``--model <name>``
    | **Model name** for computing subtitle similarity.
    
    *Default*: ``LaBSE``

    *Example*:

    .. code-block:: bash

        duosubs merge -p primary_sub.srt -s secondary_sub.srt --model Qwen/Qwen3-Embedding-0.6B

    .. tip::
        Pick one from 
        `🤗 Hugging Face <https://huggingface.co/models?library=sentence-transformers>`_  or 
        check out from `leaderboard <https://huggingface.co/spaces/mteb/leaderboard>`_ for 
        top performing model.

        .. warning::

            -   Some models may require significant RAM or GPU (VRAM) to run and might not
                be compatible with all devices — especially larger models. 
            -   Please ensure the selected model supports your desired language for reliable 
                results.

-   | ``--device <choice>``
    | Choose the **compute device** for running the model.

    Choices:

    - ``cpu`` — run on CPU
    - ``cuda`` — run on NVIDIA (Windows, Linux) or AMD GPU (Linux only)
    - ``mps`` — run on Apple Silicon GPU (macOS only)
    - ``auto`` — auto-detects the best available device in this order: ``cuda`` → ``mps`` → ``cpu``

    *Default*: ``auto``

    *Example*:

    .. code-block:: bash

        duosubs merge -p primary_sub.srt -s secondary_sub.srt --device cpu

    .. tip::
        Use ``cuda`` or ``mps`` for best performance.

-   | ``--batch-size <integer>``
    | **Number of subtitle lines** (more than 0) to process in **parallel** during embedding.

    *Default*: ``32``

    *Example*:

    .. code-block:: bash

        duosubs merge -p primary_sub.srt -s secondary_sub.srt --batch-size 128

    .. tip::
        Larger values are faster but use more memory.

-   | ``--model-precision <choice>``
    | Set the **precision mode** for model inference.

    Available choices:

    - ``float32`` — full precision (default; highest accuracy)
    - ``float16`` — half precision
    - ``bfloat16`` — half precision with the same range as float32

    *Default*: ``float32``

    *Example*:

    .. code-block:: bash

        duosubs merge -p primary_sub.srt -s secondary_sub.srt --model-precision float16

    .. tip::
        Lower precision modes such as ``float16`` and ``bfloat16`` can significantly 
        **reduce memory** usage and **speed up** processing, especially on supported GPUs:

          - ``float16`` is widely supported on modern GPUs, but may suffer from **overflow** or **instability** in some cases due to its limited numeric range.
          - ``bfloat16`` offers **better** numerical **stability** by preserving the same dynamic range as ``float32``, but is only available on **newer hardware** like Ampere GPUs and TPUs.

        .. warning::
                These modes may lead to slightly **reduced semantic accuracy**, depending on the 
                model and content, especially in edge cases.

Alignment Behavior
^^^^^^^^^^^^^^^^^^^

.. _ignore-non-overlap-filter:

-   | ``--ignore-non-overlap-filter``
    | **Ignore** the step of **extracting** and **filtering non-overlap subtitle**. 

    *Default*: ``--no-ignore-non-overlap-filter``

    *Example*:

    .. code-block:: bash

        duosubs merge -p primary_sub.srt -s secondary_sub.srt --ignore-non-overlap-filter

    .. tip::
        This option is only **applicable** when **some** or **all**  of the matching lines from 
        both subtitles are **not overlapped**. 

        If this is **not** the case, please **do not enable** this option.

        See :ref:`known limitations <known-limitations>` for more details.

Output Styling
^^^^^^^^^^^^^^^

-   | ``--retain-newline``
    | **Retain "\\N"** line breaks from the original subtitles.

    *Default*: ``--no-retain-newline``

    *Example*:

    .. code-block:: bash

        duosubs merge -p primary_sub.srt -s secondary_sub.srt --retain-newline

-   | ``--secondary-above``
    | The **secondary** subtitle lines are placed **above** the **primary** subtitle lines, but the timing is based on the primary subtitles.

    *Default*: ``--no-secondary-above``

    *Example*:

    .. code-block:: bash

        duosubs merge -p primary_sub.srt -s secondary_sub.srt --secondary-above

Output Files
^^^^^^^^^^^^^

-   | ``--omit <choice...>``
    | **List of files** to **omit** from the output zip.

    Choices:

    - ``none`` — No file is omitted
    - ``combined`` — Combined primary and secondary subtitle file
    - ``primary`` — Primary subtitle file
    - ``secondary`` — Time-shifted secondary subtitle file
    - ``edit`` — Edit file (e.g., for project or intermediate data)

    *Default*: ``edit``

    *Example*:

    .. code-block:: bash

        duosubs merge -p primary_sub.srt -s secondary_sub.srt --omit edit --omit primary --omit secondary

    .. note::

        If you are **not** using limited shells like Windows **CMD** or **Powershell**, 
        use the following shorter code instead:

        .. code-block:: bash

            duosubs merge -p primary_sub.srt -s secondary_sub.srt --omit edit primary secondary


-   | ``--format-all <choice>``
    | Sets the **format** for **all** generated subtitle files (affected by ``--omit`` options).

    Choices:
    
    - ``srt`` — SubRip subtitle format
    - ``vtt`` — WebVTT subtitle format
    - ``mpl2`` — MPL2 subtitle format
    - ``ttml`` — Timed Text Markup Language format
    - ``ass`` — Advanced SubStation Alpha format
    - ``ssa`` — SubStation Alpha format

    *Default*: ``ass``

    *Example*:
    
    .. code-block:: bash

        duosubs merge -p primary_sub.srt -s secondary_sub.srt --format-all vtt

-   | ``--format-combined <choice>``
    | Sets the **format** for the generated **merged** subtitle file, **overriding** what's set in ``--format-all``.

    Choices:

    - ``srt`` — SubRip subtitle format
    - ``vtt`` — WebVTT subtitle format
    - ``mpl2`` — MPL2 subtitle format
    - ``ttml`` — Timed Text Markup Language format
    - ``ass`` — Advanced SubStation Alpha format
    - ``ssa`` — SubStation Alpha format

    *Default*: ``None``

    *Example*:
    
    .. code-block:: bash

        duosubs merge -p primary_sub.srt -s secondary_sub.srt --format-combined vtt

-   | ``--format-primary <choice>``
    | Sets the **format** for the generated **primary** subtitle file, **overriding** what's set in ``--format-all``.

    Choices:

    - ``srt`` — SubRip subtitle format
    - ``vtt`` — WebVTT subtitle format
    - ``mpl2`` — MPL2 subtitle format
    - ``ttml`` — Timed Text Markup Language format
    - ``ass`` — Advanced SubStation Alpha format
    - ``ssa`` — SubStation Alpha format

    *Default*: `None`

    *Example*:
    
    .. code-block:: bash

        duosubs merge -p primary_sub.srt -s secondary_sub.srt --format-primary vtt

-   | ``--format-secondary <choice>``
    | Sets the **format** for the generated **secondary** subtitle file, **overriding** what's set in ``--format-all``.

    Choices:
    
    - ``srt`` — SubRip subtitle format
    - ``vtt`` — WebVTT subtitle format
    - ``mpl2`` — MPL2 subtitle format
    - ``ttml`` — Timed Text Markup Language format
    - ``ass`` — Advanced SubStation Alpha format
    - ``ssa`` — SubStation Alpha format

    *Default*: `None`

    *Example*:
    
    .. code-block:: bash

        duosubs merge -p primary_sub.srt -s secondary_sub.srt --format-secondary vtt

-   | ``--output-name <name>``
    | Set the **base name** for output files (without extension).

    *Default*: Primary subtitle's base name

    *Example*:
    
    .. code-block:: bash

        duosubs merge -p primary_sub.srt -s secondary_sub.srt --output-name processed_sub

-   | ``--output-dir``
    | Set the **output directory**.

    *Default*: Primary subtitle's location (can be absolute or relative path)

    *Example*:
    
    .. code-block:: bash

        duosubs merge -p primary_sub.srt -s secondary_sub.srt --output-dir "D:\Users\Name\Documents\Folder"

Miscellaneous
^^^^^^^^^^^^^^

-   | ``--help``
    | Show **help message** of the ``merge`` command and exit.

    *Example*:
    
    .. code-block:: bash

        duosubs merge --help
