DuoSubs
=======

.. raw:: html

   <div>
      <div style="display: flex; justify-content: start; gap: 5px; flex-wrap: wrap; margin-top: 1em;">
         <a href="https://github.com/CK-Explorer/DuoSubs" target="_blank">
               <img src="https://img.shields.io/github/stars/CK-Explorer/DuoSubs?style=social" />
         </a>
         <a href="https://pypi.org/project/duosubs/" target="_blank">
               <img src="https://img.shields.io/pypi/v/duosubs.svg" />
         </a>
         <a href="https://pypi.org/project/duosubs/" target="_blank">
               <img src="https://img.shields.io/pypi/pyversions/duosubs.svg" />
         </a>
               <a href="https://github.com/CK-Explorer/DuoSubs/blob/main/LICENSE" target="_blank">
               <img src="https://img.shields.io/badge/license-Apache--2.0-blueviolet.svg" />
         </a>
      </div>
      <p></p>
   </div>

Merging subtitles using only the nearest timestamp often leads to incorrect pairings
— lines may end up out of sync, duplicated, or mismatched.

This Python tool uses **semantic similarity** 
(via `Sentence Transformers <https://www.sbert.net/>`_) to align subtitle lines based 
on **meaning** instead of timestamps — making it possible to pair subtitles across **different 
languages**.

Features
--------

- 📌 Aligns subtitle lines based on **meaning**, not timing
- 🌍 **Multilingual** support based on the user selected `model <https://huggingface.co/models?library=sentence-transformers>`_
- 📄 Flexible format support — works with **SRT**, **VTT**, **MPL2**, **TTML**, **ASS**, **SSA** files
- 🧩 Easy-to-use **Python API** for integration
- 💻 **Command-line interface** with customizable options
- 🌐 **Web UI** — run **locally** or in the **cloud** via |Colab| or |HF_Spaces|

.. |Colab| image:: https://colab.research.google.com/assets/colab-badge.svg
     :target: https://colab.research.google.com/github/CK-Explorer/DuoSubs/blob/main/notebook/DuoSubs-webui.ipynb
     :alt: Colab

.. |HF_Spaces| image:: https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-orange
     :target: https://huggingface.co/spaces/CK-Explorer/DuoSubs
     :alt: HF_Spaces

License
--------

This tool is licensed under 
`Apache-2.0 license <https://github.com/CK-Explorer/DuoSubs/blob/main/LICENSE>`_.


.. toctree::
   :maxdepth: 2
   :caption: Getting Started
   :hidden:

   getting_started/cloud_deployment
   getting_started/local_deployment

.. toctree::
   :maxdepth: 2
   :caption: Design & Limitations
   :hidden:

   design_and_limitations/design

.. toctree::
   :maxdepth: 2
   :caption: CLI Usage
   :hidden:

   cli_usage/usage
   cli_usage/launch_webui
   cli_usage/merge
   cli_usage/miscellaneous

.. toctree::
   :maxdepth: 2
   :caption: API Usage
   :hidden:

   api_usage/web_ui_launching
   api_usage/core_subtitle_merging

.. toctree::
   :maxdepth: 2
   :caption: API References
   :hidden:

   api_references/web_ui_launching
   api_references/core_subtitle_merging

.. toctree::
   :maxdepth: 1
   :caption: Release Notes
   :hidden:

   release_notes
