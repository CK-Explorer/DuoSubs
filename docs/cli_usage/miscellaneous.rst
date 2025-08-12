Miscellaneous Options
======================

.. _install-completion:

-   | ``--install-completion``
    | **Install** shell **tab-completion** support for this CLI tool.

    After running, restart your shell to activate it.

    Optional Add-on (specify shell):

    - ``bash``
    - ``zsh``
    - ``fish``
    - ``powershell``

    *Example*:
    
    .. code-block:: bash

        duosubs --install-completion`bash

.. _show-completion:

-   | ``--show-completion``
    | **Show shell completion script** for the current shell (without installing).
    
    Useful for manual integration or debugging.

    *Example*:
    
    .. code-block:: bash
        
        duosubs --show-completion

.. _help:

-   | ``--help``
    | Show **help message** and exit.

    It can also be used with ``merge`` and ``launch-webui`` commands.

    *Examples*:

    .. code-block:: bash

        duosubs --help

    .. code-block:: bash

        duosubs launch-webui --help

    .. code-block:: bash

        duosubs merge --help
