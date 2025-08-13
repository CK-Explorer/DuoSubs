
"""
Utility functions for web UI testing: free port selection and server readiness polling.
"""

import socket
import time

import requests


def get_free_port() -> int:
    """
    Find and return a free port on the local machine.

    Returns:
        int: An available port number.
    """
    s = socket.socket()
    s.bind(('', 0))
    port = int(s.getsockname()[1])
    s.close()
    return port

def wait_for_server(url: str, timeout: float = 20) -> bool:
    """
    Poll the server until it's ready (HTTP 200) or timeout is reached.

    Args:
        url (str): The server URL to poll.
        timeout (float): Maximum time to wait in seconds.

    Returns:
        bool: True if the server became ready within the timeout.

    Raises:
        RuntimeError: If the server did not become ready in time.
    """
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url)
            if r.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(0.25)
    raise RuntimeError(f"Server at {url} didn't become ready in {timeout} seconds")
