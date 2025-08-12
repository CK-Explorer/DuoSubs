Web UI Launching
=================

``DuoSubs`` Web UI is built using `Gradio <https://www.gradio.app/>`_. Since
:meth:`duosubs.create_duosubs_gr_blocks` is a ``gradio.Blocks`` instance, you can use 
any method available in ``gradio.Blocks``, see 
`Gradio Blocks Docs <https://www.gradio.app/docs/gradio/blocks>`_.

Run the Server over HTTPS
--------------------------

The following example demonstrates how to create ``webui`` as a ``gradio.Blocks`` instance 
from :meth:`duosubs.create_duosubs_gr_blocks`, and use its built-in methods,
like ``queue`` and ``launch`` to start the web server with the SSL-encryption enabled.

.. code-block:: python

    from duosubs import create_duosubs_gr_blocks

    # Build the Web UI layout (Gradio Blocks)
    webui = create_duosubs_gr_blocks() 

    webui.queue(default_concurrency_limit=None) # Allow unlimited concurrent requests
    webui.launch(
        server_name="0.0.0.0",      # Assign host address
        server_port=8000,           # Assign port number
        ssl_keyfile="/path/to/privkey.pem", # Path to SSL keyfile
        ssl_certfile="/path/to/cert.pem",   # Path to SSL cert
        ssl_verify=False,           # Skip certificate validation
        inbrowser=True              # Automatically launch in a new tab
    )

.. note::

    Despite ``gradio.Blocks`` provides built-in authentication support via its ``auth``
    parameter, this mechanism is **basic** and **not suitable** for production environments. 
    
    For **stronger security**, especially when exposing the Web UI publicly, it is recommended 
    to use a **reverse proxy** (e.g., Nginx or Apache) with robust authentication or 
    `OAuth <https://www.gradio.app/guides/sharing-your-app#o-auth-login-via-hugging-face>`_ 
    and **HTTPS**.

Configuring Cache Deletion Frequency and Age
---------------------------------------------

``DuoSubs`` Web UI stores uploaded and merged files in its cache directory.
To automatically clean up old cache files, set the parameters 
``cache_delete_frequency`` and ``cache_delete_age`` in :meth:`duosubs.create_duosubs_gr_blocks`.

In the example below, ``cache_delete_frequency`` is set to 3600 seconds (1 hour) and 
``cache_delete_age`` to 7200 seconds (2 hours). This means the server will scan the 
cache every hour and delete any files older than 2 hours.

.. code-block:: python

    from duosubs import create_duosubs_gr_blocks

    webui = create_duosubs_gr_blocks(
        cache_delete_frequency=3600,    # Scan every hours
        cache_delete_age=7200           # Delete cached files older than 2 hours
    ) 

    webui.queue(default_concurrency_limit=None)
    webui.launch(inbrowser=True)

.. warning::
 
    Cached data may remain if the server stops unexpectedly, and you may need to delete them 
    manually.
