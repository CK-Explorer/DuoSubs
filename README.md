# 🎬 DuoSubs

[![codecov](https://codecov.io/gh/CK-Explorer/DuoSubs/branch/main/graph/badge.svg)](https://codecov.io/gh/CK-Explorer/DuoSubs)

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

First, install the correct version of PyTorch by following the official instructions: 
https://pytorch.org/get-started/locally

Then, install this repo via pip:
```bash
pip install duosubs
```

---

## 🚀 Usage

Here are the simplest way to get started:

- via command line

    ```bash
    duosubs -p primary_file.srt --s secondary_file.srt
    ```

- via Python API

    ```python
    from duosubs import MergeArgs, run_merge_pipeline

    # Store all arguments
    args = MergeArgs(
        primary="sub_lang_1.srt",
        secondary="sub_lang_2.ass"
    )

    # Load, merge, and save subtitles.
    run_merge_pipeline(args, print)
    ```

By default, the Sentence Transformer model used is 
[LaBSE](https://huggingface.co/sentence-transformers/LaBSE).

If you want to experiment with different models, then pick one from
[🤗 Hugging Face](https://huggingface.co/models?library=sentence-transformers) 
or check out from the
[leaderboard](https://huggingface.co/spaces/mteb/leaderboard)
for top performing model.

For example, if the model chosen is 
[Qwen/Qwen3-Embedding-4B](https://huggingface.co/Qwen/Qwen3-Embedding-4B), 
you can run:

- via command line

    ```bash
    duosubs -p primary_file.srt -s secondary_file.srt --model Qwen/Qwen3-Embedding-4B
    ```

- via Python API

    ```python
    from duosubs import MergeArgs, run_merge_pipeline

    # Store all arguments
    args = MergeArgs(
        primary="sub_lang_1.srt",
        secondary="sub_lang_2.ass",
        model="Qwen/Qwen3-Embedding-4B"
    )

    # Load, merge, and save subtitles.
    run_merge_pipeline(args, print)
    ```

To learn more about this tool, please see the [documentation]().

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

- The **accuracy** of the merging process **varies** on the model selected.
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
- [lingua](https://github.com/pemistahl/lingua-py) — for detecting the subtitles' language codes
- [pysubs2](https://github.com/tkarabela/pysubs2) — for subtitle file I/O utilities
- [charset_normalizer](https://github.com/jawah/charset_normalizer) — for identifying the file 
encoding
- [typer](https://github.com/fastapi/typer) — for CLI application
- [tqdm](https://github.com/tqdm/tqdm) — for displaying progress bar
- [Tears of Steel](https://mango.blender.org/) — subtitles used for testing and development 
purposes

---

## 🤝 Contributing

Contributions are welcome! If you'd like to submit a pull request, please check out the
 [contributing guidelines](CONTRIBUTING.md).

---

## 🔑 License

Apache-2.0 license - see the [LICENSE](LICENSE) file for details.
