DuoSubs
=======

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
- 🧩 Easy-to-use **API** for integration
- 💻 **Command-line interface** with customizable options
- 📄 Flexible format support — works with **SRT**, **VTT**, **MPL2**, **TTML**, **ASS**, **SSA** files

Documentation
-------------

.. toctree::
   :maxdepth: 3
   :caption: Documentation:

   getting_started
   design
   cli
   api_usage
   api_references
   changelog

License
--------

This tool is licensed under 
`Apache-2.0 license <https://github.com/CK-Explorer/DuoSubs/blob/main/LICENSE>`_.
