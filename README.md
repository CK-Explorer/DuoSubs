# 🎬 DuoSubs

[![CI](https://github.com/CK-Explorer/DuoSubs/actions/workflows/ci.yml/badge.svg)](https://github.com/CK-Explorer/DuoSubs/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/duosubs.svg)](https://pypi.org/project/duosubs/)
[![Python Versions](https://img.shields.io/pypi/pyversions/duosubs.svg)](https://pypi.org/project/duosubs/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blueviolet.svg)](/LICENSE)
[![Type Checked: Mypy](https://img.shields.io/badge/type%20checked-mypy-blue)](http://mypy-lang.org/)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-blue?logo=python&labelColor=gray)](https://github.com/astral-sh/ruff)
[![codecov](https://codecov.io/gh/CK-Explorer/DuoSubs/branch/main/graph/badge.svg)](https://codecov.io/gh/CK-Explorer/DuoSubs)
[![Documentation Status](https://readthedocs.org/projects/duosubs/badge/?version=latest)](https://duosubs.readthedocs.io/en/latest/?badge=latest)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/CK-Explorer/DuoSubs/blob/main/notebook/DuoSubs-webui.ipynb)
[![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-orange)](https://huggingface.co/spaces/CK-Explorer/DuoSubs)

Merging subtitles using only the nearest timestamp often leads to incorrect pairings
— lines may end up out of sync, duplicated, or mismatched.

This Python tool uses **semantic similarity** 
(via [Sentence Transformers](https://www.sbert.net/)) to align subtitle lines based on 
**meaning** instead of timestamps — making it possible to pair subtitles across 
**different languages**.

---

## ✨ Features

- 📌 Aligns subtitle lines based on **meaning**, not timing
- 🌍 **Multilingual** support based on the **user** selected 
[Sentence Transformer model](https://huggingface.co/models?library=sentence-transformers)
- 📄 Flexible format support — works with **SRT**, **VTT**, **MPL2**, **TTML**, **ASS**, 
**SSA** files
- 🧩 Easy-to-use **Python API** for integration
- 💻 **Command-line interface** with customizable options
- 🌐 **Web UI** — run locally or in the cloud via 
[Google Colab](https://colab.research.google.com/github/CK-Explorer/DuoSubs/blob/main/notebook/DuoSubs-webui.ipynb)
or 
[Hugging Face Spaces](https://huggingface.co/spaces/CK-Explorer/DuoSubs)

---

## ☁️ Cloud Deployment

You can launch the Web UI instantly without installing anything locally by running it in the cloud.

- [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/CK-Explorer/DuoSubs/blob/main/notebook/DuoSubs-webui.ipynb)
- [![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-orange)](https://huggingface.co/spaces/CK-Explorer/DuoSubs)

> [!NOTE]
> - Google Colab has a limited runtime allocation, especially when using the free instance.
> - On Hugging Face Spaces, only a few models are preloaded, and inference can be slower because it runs on CPU.

---

## 💻 Local Deployment

### 🛠️ Installation

1. Install the correct version of PyTorch for your system by following the official 
instructions: https://pytorch.org/get-started/locally
2. Install this repo via pip:
    ```bash
    pip install duosubs
    ```

### 🚀 Usage

#### 🌐 Launch Web UI Locally

You can launch the web UI locally:

- via command line

    ```bash
    duosubs launch-webui
    ```

- via Python API

    ```python
    from duosubs import create_duosubs_gr_blocks

    # Build the Web UI layout (Gradio Blocks)
    webui = create_duosubs_gr_blocks() 

    # These commands work just like launching a regular Gradio app
    webui.queue(default_concurrency_limit=None) # Allow unlimited concurrent requests
    webui.launch(inbrowser=True)                # Start the Web UI and open it in a browser tab
    ```

This starts the server, prints its url (e.g. http://127.0.0.1:7860), and then opens the Web UI
in a new browser tab.

If you want to launch it in other url (e.g. 0.0.0.0) and port (e.g 8000), you can run:

- via command line

    ```bash
    duosubs launch-webui --host 0.0.0.0 --port 8000
    ```

- via Python API

    ```python
    from duosubs import create_duosubs_gr_blocks

    webui = create_duosubs_gr_blocks() 

    webui.queue(default_concurrency_limit=None)
    webui.launch(
        server_name = "0.0.0.0",    # use different address
        server_port = 8000,         # use different port number
        inbrowser=True
    )
    ```

> [!WARNING]
> - The Web UI caches files during processing, and clears files older than 2 hours every 1 hour. Cached data may remain if the server stops unexpectedly.
> - Sometimes, older model may fail to be released after switching or closing sessions. If you run out of RAM or VRAM, simply restart the script.

To learn more about the launching options, please see the sections of 
[Launch Web UI Command](https://duosubs.readthedocs.io/en/latest/cli_usage/launch_webui.html)
and [Web UI Launching](https://duosubs.readthedocs.io/en/latest/api_usage/web_ui_launching.html)
in the [documentation](https://duosubs.readthedocs.io/en/latest/).

#### 💻 Merge Subtitles

With the [demo files](/demo/) provided, here are the simplest way to merge the subtitles:

- via command line

    ```bash
    duosubs merge -p demo/primary_sub.srt -s demo/secondary_sub.srt
    ```

- via Python API

    ```python
    from duosubs import MergeArgs, run_merge_pipeline

    # Store all arguments
    args = MergeArgs(
        primary="demo/primary_sub.srt",
        secondary="demo/secondary_sub.srt"
    )

    # Load, merge, and save subtitles.
    run_merge_pipeline(args, print)
    ```

These codes will produce [primary_sub.zip](/demo/primary_sub.zip), with the following structure:

```text
primary_sub.zip
├── primary_sub_combined.ass   # Merged subtitles
├── primary_sub_primary.ass    # Original primary subtitles
└── primary_sub_secondary.ass  # Time-shifted secondary subtitles
```

By default, the Sentence Transformer model used is 
[LaBSE](https://huggingface.co/sentence-transformers/LaBSE).

If you want to experiment with different models, then pick one from
[🤗 Hugging Face](https://huggingface.co/models?library=sentence-transformers) 
or check out from the
[leaderboard](https://huggingface.co/spaces/mteb/leaderboard)
for top performing model.

For example, if the model chosen is 
[Qwen/Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B), 
you can run:

- via command line

    ```bash
    duosubs merge -p demo/primary_sub.srt -s demo/secondary_sub.srt --model Qwen/Qwen3-Embedding-0.6B
    ```

- via Python API

    ```python
    from duosubs import MergeArgs, run_merge_pipeline

    # Store all arguments
    args = MergeArgs(
        primary="demo/primary_sub.srt",
        secondary="demo/secondary_sub.srt",
        model="Qwen/Qwen3-Embedding-0.6B"
    )

    # Load, merge, and save subtitles.
    run_merge_pipeline(args, print)
    ```

- via Web UI

    > In **Configurations → Model & Device → Sentence Transformer Model**, replace `sentence-transformers/LaBSE` with `Qwen/Qwen3-Embedding-0.6B`.


> [!WARNING]
> - Some models may require significant RAM or GPU (VRAM) to run, and might not be compatible with all devices — especially larger models. 
> - Also, please ensure the selected model supports your desired language for reliable results.

Also, this tool has 3 merging modes, i.e. ``synced``, ``mixed``, and ``cuts`` modes. 
Here are some of the simple guidelines to choose the appropriate mode:

- If both subtitle files are **timestamp-synced**, use ``synced`` for the cleanest result.
- If timestamps **drift** or only **partially overlap**, use ``mixed``.
- If subtitles come from **different editions** of the video, with **primary** subtitles being 
the **extended** or **longer version**, use ``cuts``.

To merge with a specific mode (e.g. ``cuts``), run:

- via command line

    ```bash
    duosubs merge -p primary_sub.srt -s secondary_sub.srt --mode cuts
    ```

- via Python API

    ```python
    from duosubs import MergeArgs, MergingMode, run_merge_pipeline

    # Store all arguments
    args = MergeArgs(
        primary="primary_sub.srt",
        secondary="secondary_sub.srt",
        merging_mode=MergingMode.CUTS   # Modes available: MergingMode.SYNCED, MergingMode.MIXED, MergingMode.CUTS
    )

    # Load, merge, and save subtitles.
    run_merge_pipeline(args, print)
    ```

- via Web UI

    > In **Configurations** → **Alignment Behavior** → **Merging Mode**, choose ``Cuts``.


> [!TIP]
> For ``mixed`` and ``cuts`` modes, try to use subtitle files **without scene annotations** if possible, as they may reduce alignment quality.

To learn more about merging options, please see the sections of
[Merge Command](https://duosubs.readthedocs.io/en/latest/cli_usage/merge.html)
and [Core Subtitle Merging](https://duosubs.readthedocs.io/en/latest/api_usage/core_subtitle_merging.html)
in the [documentation](https://duosubs.readthedocs.io/en/latest/).

---

## 📚 Behind the Scenes

1. Parse subtitles and detect language.
2. Tokenize subtitle lines.
3. Extract and filter non-overlapping subtitles (``synced`` *mode only*).
4. Estimate tokenized subtitle pairings using DTW.
5. Refine alignment using a sliding window approach with size of 3.
6. Extract and filter extended subtitles from the primary track (``cuts`` *mode only*).
7. Refine alignment using a sliding window approach with size of 2.
8. Combine aligned and non-overlapping subtitles or extended subtitles
9. Eliminate unnecessary newline within subtitle lines.

---

## 🚫 Known Limitations

- The **accuracy** of the merging process **varies** on the 
[model](https://huggingface.co/models?library=sentence-transformers) selected.
- Some models may produce **unreliable results** for **unsupported** or low-resource **languages**.
- Some sentence **fragments** from secondary subtitles may be **misaligned** to the 
primary subtitles line due to the tokenization algorithm used.
- **Secondary** subtitles might **contain extra whitespace** as a result of token-level merging.
- In ``mixed`` and ``cuts`` modes, the algorithm may **not work reliably** since matching lines have **no timestamp overlap**, and either subtitle could contain **extra** or **missing lines**.

---

## 🙏 Acknowledgements

This project wouldn't be possible without the incredible work of the open-source community. 
Special thanks to:

- [sentence-transformers](https://github.com/UKPLab/sentence-transformers) — for the semantic 
embedding backbone
- [Hugging Face](https://huggingface.co/) — for hosting models and making them easy to use
- [PyTorch](https://pytorch.org/) — for providing the deep learning framework
- [fastdtw](https://github.com/slaypni/fastdtw) — for aligning the subtitles
- [hmmlearn](https://github.com/hmmlearn/hmmlearn) — for denoising sequences
- [lingua-py](https://github.com/pemistahl/lingua-py) — for detecting the subtitles' language codes
- [pysubs2](https://github.com/tkarabela/pysubs2) — for subtitle file I/O utilities
- [charset_normalizer](https://github.com/jawah/charset_normalizer) — for identifying the file 
encoding
- [typer](https://github.com/fastapi/typer) — for CLI application
- [tqdm](https://github.com/tqdm/tqdm) — for displaying progress bar
- [gradio](https://github.com/gradio-app/gradio) — for creating Web UI application
- [Tears of Steel](https://mango.blender.org/) — subtitles used for demo, testing and development 
purposes. Created by the 
[Blender Foundation](https://mango.blender.org/), licensed under 
[CC BY 3.0](http://creativecommons.org/licenses/by/3.0/).

---

## 🤝 Contributing

Contributions are welcome! If you'd like to submit a pull request, please check out the
 [contributing guidelines](/CONTRIBUTING.md).

---

## 🔑 License

Apache-2.0 license - see the [LICENSE](/LICENSE) file for details.
