CLI Usage Format
=================

The general ``DuoSubs`` CLI usage format is:

.. code-block:: bash

   duosubs COMMAND [OPTIONS] [ARGUMENTS]

where:

- **COMMAND** — the main action to perform (e.g., ``merge``, ``launch-webui``)  
- **OPTIONS** — optional flags or parameters (e.g., ``--help``)  
- **ARGUMENTS** — positional inputs required by the command  

Main Commands & Options
=======================

**Primary commands** in the CLI are:  

- ``launch-webui`` — starts the Web UI.  
- ``merge`` — merges multiple subtitle files.  

Details for these commands with their options are available in:  
:doc:`Launch Web UI </cli_usage/launch_webui>` and 
:doc:`Merge Commands </cli_usage/merge>`.  

Also, it has the following **additional utility options**:  

- ``--install-completion`` — install shell completion scripts.  
- ``--show-completion`` — display shell completion script content.  
- ``--help`` — show general or command-specific help.  

See :doc:`Miscellaneous Options </cli_usage/miscellaneous>` for more information 
on these utilities.
