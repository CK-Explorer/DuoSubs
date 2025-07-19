Design & Limitations
=======================

This section explains how ``DuoSubs`` works behind the scenes and outlines known limitations.

How It Works
------------

``DuoSubs`` aligns two subtitle files using the following steps:

1.  | **Parse and Detect Language**
    | Subtitles are loaded, and the dominant language of each file is automatically identified.

2.  | **Tokenization**
    | Each subtitle line is tokenized using:
    |   • **punctuations** as line breaks for **space** separated languages.
    |   • **punctuations** and **whitespaces** as line breaks for **non-space** separated languages.

3.  | **Extract and filter non-overlapping subtitles** *(optional)*
    | Subtitle segments that do not overlap in time are optionally extracted and retained for later combination.

4.  | **Estimate tokenized subtitle pairings using DTW**  
    | For segments with overlapping timestamps, the pairing is estimated using Dynamic Time Warping (DTW), based on semantic similarity between tokenized texts.

5.  | **Refine alignment using a sliding window approach**
    | The initial alignment is adjusted using local neighborhood context in a sliding window to improve semantic continuity.

6.  | **Combine aligned and non-overlapping subtitles**
    | The aligned overlapping segments are merged with the filtered non-overlapping ones to produce a coherent bilingual subtitle track.

7.  | **Eliminate Unnecessary Newline** 
    | The unnecessary extra newlines are cleaned in subtitle texts.

.. _known-limitations:

Known Limitations
-----------------

-   The **accuracy** of the merging process **varies** on the 
    `model <https://huggingface.co/models?library=sentence-transformers>`_ selected.
-   Some sentence **fragments** from secondary subtitles may be **misaligned** to the primary 
    subtitles line due to the tokenization algorithm used.
-   **Secondary** subtitles might **contain extra whitespace** as a result of token-level 
    merging.
-   The algorithm may **not** work reliably if the **timestamps** of some matching lines 
    **don't overlap** at all.

    .. tip::

        If both subtitle files are **known** to be **perfectly semantically aligned**,
        meaning:

          - **matching dialogue contents**
          - **no extra lines** like scene annotations or bonus Director's Cut stuff.

        Then, by **enabling** the ``ignore-non-overlap-filter`` option in either case:

          - :ref:`command-line interface <ignore-non-overlap-filter>`
          - :meth:`duosubs.MergeArgs`
          - :meth:`duosubs.Merger.merge_subtitle`

        to skip the overlap check — the merge should go smoothly from there.

        ⚠️ If the subtitle **timings** are **off** and the two subtitle files 
        **don't fully match in content**, the algorithm likely **won't** produce great results. 
        Still, you can try merging them with ``ignore-non-overlap-filter`` **enabled**.
