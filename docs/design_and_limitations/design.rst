Behind the Scenes
==================

``DuoSubs`` aligns two subtitle files using the following steps:

1.  | **Parse and Detect Language**
    | Subtitles are loaded, and the dominant language of each file is automatically identified.

.. _tokenization:

2.  | **Tokenization**
    | Each subtitle line is tokenized using:
    |   • **punctuations** as line breaks for **space** separated languages.
    |   • **punctuations** and **whitespaces** as line breaks for **non-space** separated languages.

3.  | **Extract and filter non-overlapping subtitles** (``synced`` *mode only*)
    | Subtitle segments that do not overlap in time are optionally extracted and retained for later combination.

4.  | **Estimate tokenized subtitle pairings using DTW**  
    | For segments with overlapping timestamps, the pairing is estimated using Dynamic Time Warping (DTW), based on semantic similarity between tokenized texts.

5.  | **Refine alignment using a sliding window approach**
    | The initial alignment is adjusted using local neighborhood context in a sliding window with a size of 3. This step is important because the DTW-based pairing may result in duplicate secondary subtitles.

6.  | **Extract and filter extended subtitles from the primary track** (``cuts`` *mode only*)
    | Identifies extended subtitle spans with HMM-denoised binary masks, then extract them using progressive similarity filtering.

7.  | **Refine alignment using a sliding window approach**
    | The alignment is adjusted again in a sliding window with a size of 2 subtitle segments to achieve a better result.

8.  | **Combine aligned and non-overlapping subtitles or extended subtitles**
    | The aligned overlapping segments are merged with the filtered non-overlapping ones to produce a coherent bilingual subtitle track.

9.  | **Eliminate Unnecessary Newline** 
    | The unnecessary extra newlines are cleaned in subtitle texts.

Known Limitations
==================

-   The **accuracy** of the merging process **varies** on the 
    `model <https://huggingface.co/models?library=sentence-transformers>`_ selected.
-   Some models may produce **unreliable results** for **unsupported** or low-resource **languages**.
-   Some sentence **fragments** from secondary subtitles may be **misaligned** to the primary 
    subtitles line due to the :ref:`tokenization algorithm <tokenization>` used.
-   **Secondary** subtitles might **contain extra whitespace** as a result of token-level 
    merging.
-   In ``mixed`` and ``cuts`` modes, the algorithm may **not work reliably** since matching lines 
    have **no timestamp overlap**, and either subtitle could contain **extra** or **missing lines**.
