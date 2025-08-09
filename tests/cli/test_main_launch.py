
"""
CLI integration and validation tests for the `launch-webui` command of duosubs subtitle 
merging tool.

Tests invalid CLI options, server startup, and helper utilities.
"""

import multiprocessing
import random

from typer.testing import CliRunner

from duosubs.cli.main import app
from tests.common_utils.utils import strip_ansi
from tests.webui.common_utils.utils import get_free_port, wait_for_server

runner = CliRunner()

# ----------------------------
# Invalid Option Tests
# ----------------------------

def test_invalid_lower_port_number() -> None:
    """
    Test that providing a port number below the valid range fails.
    """
    lower_random_port = random.randint(-65535, 1023)
    result = runner.invoke(app, ["launch-webui", "--port", str(lower_random_port)])
    assert result.exit_code != 0
    assert "Invalid value for '--port'" in strip_ansi(result.output)

def test_invalid_higher_port_number() -> None:
    """
    Test that providing a port number above the valid range fails.
    """
    upper_random_port = random.randint(65536, 100000)
    result = runner.invoke(app, ["launch-webui", "--port", str(upper_random_port)])
    assert result.exit_code != 0
    assert "Invalid value for '--port'" in strip_ansi(result.output)

def test_invalid_cache_delete_frequency() -> None:
    """
    Test that providing a negative cache delete frequency fails.
    """
    random_frequency = random.randint(-10000, 0)
    result = runner.invoke(app, [
        "launch-webui", 
        "--cache-delete-freq", str(random_frequency)
        ]
    )
    assert result.exit_code != 0
    assert "Invalid value for '--cache-delete-freq'" in strip_ansi(result.output)

def test_invalid_cache_delete_age() -> None:
    """
    Test that providing a negative cache delete age fails.
    """
    random_age = random.randint(-10000, 0)
    result = runner.invoke(app, ["launch-webui", "--cache-delete-age", str(random_age)])
    assert result.exit_code != 0
    assert "Invalid value for '--cache-delete-age'" in strip_ansi(result.output)

# ----------------------------
# Launching Server Tests
# ----------------------------

def test_server_launch() -> None:
    """
    Test that the server launches and responds on a free port.
    """
    port = get_free_port()
    proc = multiprocessing.Process(target=run_gradio_web_ui, args=(port,), daemon=True)
    proc.start()
    try:
        assert wait_for_server(f"http://127.0.0.1:{port}/", timeout=30)
    finally:
        proc.terminate()
        proc.join()

# ----------------------------
# Helper functions
# ----------------------------

def run_gradio_web_ui(port: int) -> None:
    """
    Run the Gradio web UI app on the specified port.
    """
    app(args=["launch-webui", "--port", str(port), "--no-inbrowser",])
