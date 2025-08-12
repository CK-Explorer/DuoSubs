Launch Web UI Command
======================

The ``launch-webui`` command starts the ``DuoSubs`` Web UI, and it can be run 
without any additional option as follows:

.. code-block:: bash

    duosubs launch-webui

.. note::

    This CLI tool offers only **basic launch options**. For **advanced features** — 
    such as SSL encryption or password protection — consider using a **reverse proxy**
    or **adding the necessary options** directly to the launch command in your 
    **Python code**.

Optional Options
-----------------

Use these flags to fine-tune the Web UI’s connection, visibility, and caching.

Server Options
^^^^^^^^^^^^^^^

-   | ``--host <address>``
    | **Host** to bind the server.

    .. tip::

        You can use the following address:

            - ``localhost`` or ``127.0.0.1`` – accessible only from your computer
            - ``0.0.0.0`` – Accessible from other devices on the same network

        .. warning::

            Using ``0.0.0.0`` exposes the server to your local network and potentially 
            the internet. Only use it in trusted environments.
    
    *Default*: ``127.0.0.1``

    *Example*:

    .. code-block:: bash

        duosubs launch-webui --host 0.0.0.0

-   | ``--port <port-number>``
    | **Port** (between *1024* and *65535* inclusive) to run the server on.

    *Default*: ``7860`` if available

    *Example*:

    .. code-block:: bash

        duosubs launch-webui --port 8831

Access & Behavior Options
^^^^^^^^^^^^^^^^^^^^^^^^^^

-   | ``--share``
    | Create a publicly shareable link for DuoSubs Web UI.

    See `Sharing Demos <https://www.gradio.app/guides/sharing-your-app#sharing-demos>`_
    in Gradio website for more information.

    *Default*: ``--no-share``

    *Example*:

    .. code-block:: bash

        duosubs launch-webui --share

-   | ``--inbrowser``
    | Automatically launch the ``DuoSubs`` Web UI in a new tab on the default browser.

    To disable this settings, use ``--no-inbrowser``.

    *Default*: ``--inbrowser``

    *Example*:

    .. code-block:: bash

        duosubs launch-webui --no-inbrowser

Cache Management Options
^^^^^^^^^^^^^^^^^^^^^^^^^

.. warning::

    The Web UI caches files during processing, and clears files older than 4 hours 
    every 1 hour. Cached data may remain if the server stops unexpectedly, and you may need 
    to delete them manually.

-   | ``--cache-delete-freq <frequency>``
    | **Interval** in seconds to scan and **clean up** expired cache entries.

    *Default*: 3600 seconds or 1 hour.

    *Example*:

    .. code-block:: bash

        duosubs launch-webui --cache-delete-freq 7200

-   | ``--cache-delete-age <age>``
    | **Files exceeding the specified age** (in seconds) will be **removed** from the cache.

    *Default*: 14400 seconds or 4 hours.

    *Example*:

    .. code-block:: bash

        duosubs launch-webui --cache-delete-age 7200

Miscellaneous
^^^^^^^^^^^^^^

-   | ``--help``
    | Show **help message** of the ``launch-webui`` command and exit.

    *Example*:
    
    .. code-block:: bash

        duosubs launch-webui --help
