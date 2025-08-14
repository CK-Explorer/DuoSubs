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

To learn more about the launching options, please see the 
[documentation](https://duosubs.readthedocs.io/en/latest/).

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

> [!WARNING]
> - Some models may require significant RAM or GPU (VRAM) to run, and might not be compatible with all devices — especially larger models. 
> - Also, please ensure the selected model supports your desired language for reliable results.

To learn more about this tool, please see the 
[documentation](https://duosubs.readthedocs.io/en/latest/).

---

## 📚 Behind the Scenes

1. Parse subtitles and detect language.
2. Tokenize subtitle lines.
3. Extract and filter non-overlapping subtitles. *(Optional)*
4. Estimate tokenized subtitle pairings using DTW.
5. Refine alignment using a sliding window approach.
6. Combine aligned and non-overlapping subtitles.
7. Eliminate unnecessary newline within subtitle lines.

---

## 🚫 Known Limitations

- The **accuracy** of the merging process **varies** on the 
[model](https://huggingface.co/models?library=sentence-transformers) selected.
- Some models may produce **unreliable results** for **unsupported** or low-resource **languages**.
- Some sentence **fragments** from secondary subtitles may be **misaligned** to the 
primary subtitles line due to the tokenization algorithm used.
- **Secondary** subtitles might **contain extra whitespace** as a result of token-level merging.
- The algorithm may **not** work reliably if the **timestamps** of some matching lines
**don’t overlap** at all.

> [!TIP]
> For the final known limitation, there are three possible ways to address it:
> 1. If **all** subtitle lines are completely **out of sync**, consider using another subtitle syncing tool first to align them, e.g.
>
>    - [smacke/ffsubsync](https://github.com/smacke/ffsubsync)
>    - [sc0ty/subsync](https://github.com/sc0ty/subsync)
>    - [kaegi/alass](https://github.com/kaegi/alass)
>
>    before using this tool with `ignore-non-overlap-filter` **disabled**.
>
>    Alternatively, see points 2 and 3.
>
> 2. If both subtitle files are **known** to be **perfectly semantically aligned**, meaning:
>
>    - **matching dialogue contents**
>    - **no extra lines** like scene annotations or bonus Director’s Cut stuff.
>
>    Then, just **enable** the `ignore-non-overlap-filter` option in either: 
>
>    - Web UI (`Advanced Configurations` → `Alignment Behavior`)
>    - CLI (`--ignore-non-overlap-filter`)
>    - Python API (see [documentation](https://duosubs.readthedocs.io/en/latest/))
>
>    to skip the overlap check — the merge should go smoothly from there.
>
> 3. If the subtitle **timings** are **off** and the two subtitle files **don’t fully match in content**, the algorithm likely **won’t** produce great results. Still, you can try running it with `ignore-non-overlap-filter` **enabled**.

---

## 🙏 Acknowledgements

This project wouldn't be possible without the incredible work of the open-source community. 
Special thanks to:

- [sentence-transformers](https://github.com/UKPLab/sentence-transformers) — for the semantic 
embedding backbone
- [Hugging Face](https://huggingface.co/) — for hosting models and making them easy to use
- [PyTorch](https://pytorch.org/) — for providing the deep learning framework
- [fastdtw](https://github.com/slaypni/fastdtw) — for aligning the subtitles
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
