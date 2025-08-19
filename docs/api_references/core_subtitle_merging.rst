Core Subtitle Merging
======================

This section documents the **public API** for **performing subtitle merges** programmatically.

Subtitle Data Structures
------------------------

These classes represent structured subtitle information used throughout the system.

.. autoclass:: duosubs.SubtitleData
   :members:

.. autoclass:: duosubs.SubtitleField
   :members:


Subtitle Merging Pipeline
--------------------------

High-level functions and configuration classes for merging subtitles, including the 
main entry point and step-by-step processing stages.

Pipeline Configuration Options
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: duosubs.MergeArgs
    :members:

Complete Merge Pipeline
^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: duosubs.run_merge_pipeline

Step-by-Step Pipeline Functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: duosubs.load_subtitles
.. autofunction:: duosubs.load_sentence_transformer_model
.. autofunction:: duosubs.merge_subtitles
.. autofunction:: duosubs.save_subtitles_in_zip

Advanced and Low-Level Utilities
---------------------------------

Detailed classes and functions for advanced merging, direct file I/O, and in-memory 
operations.

Core Subtitle Merging Algorithm
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: duosubs.Merger
    :members:

Subtitle File Loading Utilities
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: duosubs.load_file_edit

.. autofunction:: duosubs.load_subs

Subtitle File Writing Utilities
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: duosubs.save_file_combined

.. autofunction:: duosubs.save_file_edit

.. autofunction:: duosubs.save_file_separate

.. autofunction:: duosubs.save_memory_combined

.. autofunction:: duosubs.save_memory_edit

.. autofunction:: duosubs.save_memory_separate

Exception Classes
-----------------

Custom exceptions for error handling during subtitle loading, model inference, merging, and 
saving.

.. autoclass:: duosubs.LoadSubsError
    :members:
    :show-inheritance:

.. autoclass:: duosubs.LoadModelError
    :members:
    :show-inheritance:

.. autoclass:: duosubs.MergeSubsError
    :members:
    :show-inheritance:

.. autoclass:: duosubs.SaveSubsError
    :members:
    :show-inheritance:

Configuration Enums
-------------------

Enumerations for device selection, model precision, file omission, and supported subtitle formats.

.. autoclass:: duosubs.DeviceType
    :members:

.. autoclass:: duosubs.ModelPrecision
    :members:

.. autoclass:: duosubs.MergingMode
    :members:

.. autoclass:: duosubs.OmitFile
    :members:

.. autoclass:: duosubs.SubtitleFormat
    :members:
