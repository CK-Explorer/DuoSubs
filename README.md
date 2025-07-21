# 🎬 DuoSubs

[![CI](https://github.com/CK-Explorer/DuoSubs/actions/workflows/ci.yml/badge.svg)](https://github.com/CK-Explorer/DuoSubs/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/duosubs.svg)](https://pypi.org/project/duosubs/)
[![Python Versions](https://img.shields.io/pypi/pyversions/duosubs.svg)](https://pypi.org/project/duosubs/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blueviolet.svg)](LICENSE)
[![Type Checked: Mypy](https://img.shields.io/badge/type%20checked-mypy-blue)](http://mypy-lang.org/)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-blue?logo=python&labelColor=gray)](https://github.com/astral-sh/ruff)
[![codecov](https://codecov.io/gh/CK-Explorer/DuoSubs/branch/main/graph/badge.svg)](https://codecov.io/gh/CK-Explorer/DuoSubs)
[![Documentation Status](https://readthedocs.org/projects/duosubs/badge/?version=latest)](https://duosubs.readthedocs.io/en/latest/?badge=latest)

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
- 🧩 Easy-to-use **API** for integration
- 💻 **Command-line interface** with customizable options
- 📄 Flexible format support — works with **SRT**, **VTT**, **MPL2**, **TTML**, **ASS**, 
**SSA** files

---

## 🛠️ Installation

1. Install the correct version of PyTorch for system by following the official 
instructions: https://pytorch.org/get-started/locally
2. Install this repo via pip:
    ```bash
    pip install duosubs
    ```

---

## 🚀 Usage

With the [demo files](demo/) provided, here are the simplest way to get started:

- via command line

    ```bash
    duosubs -p demo/primary_sub.srt -s demo/secondary_sub.srt
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

These codes will produce [primary_sub.zip](demo/primary_sub.zip), with the following structure:

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
    duosubs -p demo/primary_sub.srt -s demo/secondary_sub.srt --model Qwen/Qwen3-Embedding-0.6B
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

> ⚠️ **Warning**  
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
**don’t overlap** at all. See [special case](#-special-case).

---

## 🧩 Special Case

For the last known limitation, if both subtitle files are **known** to be 
**perfectly semantically aligned**, meaning:

* **matching dialogue contents**
* **no extra lines** like scene annotations or bonus Director’s Cut stuff.

Then, just **enable** the `--ignore-non-overlap-filter` CLI option to skip the overlap check — the 
merge should go smoothly from there.

⚠️ If the subtitle **timings** are **off** and the two subtitle files 
**don’t fully match in content**, the algorithm likely **won’t** produce great results. Still, 
you can try running it with `--ignore-non-overlap-filter` **enabled**.

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
- [Tears of Steel](https://mango.blender.org/) — subtitles used for demo, testing and development 
purposes. Created by the 
[Blender Foundation](https://mango.blender.org/), licensed under 
[CC BY 3.0](http://creativecommons.org/licenses/by/3.0/).

---

## 🤝 Contributing

Contributions are welcome! If you'd like to submit a pull request, please check out the
 [contributing guidelines](CONTRIBUTING.md).

---

## 🔑 License

Apache-2.0 license - see the [LICENSE](LICENSE) file for details.
