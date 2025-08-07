"""
CLI integration and validation tests for the `merge` command of duosubs subtitle 
merging tool.

This module tests the Typer CLI app for argument validation, file handling, error 
propagation, logger output, and functional smoke tests.
"""
from pathlib import Path
from typing import Any, Callable

import pytest
from typer.testing import CliRunner

from duosubs.cli.main import app
from duosubs.common.exceptions import LoadModelError
from tests.common_utils.utils import strip_ansi

# Test subtitle paths
SUB_PATH = Path(__file__).parent / "data"

runner = CliRunner()

# ------------------------
# CLI Validation Tests
# ------------------------

def test_missing_required_arguments() -> None:
    """
    Test that missing required CLI arguments returns an error.
    """
    result = runner.invoke(app, ["merge"])
    assert result.exit_code != 0
    assert "Missing option '--primary'" in strip_ansi(result.output)

# ------------------------
# File Validation Tests
# ------------------------

def test_nonexistent_primary_file() -> None:
    """
    Test error when the primary subtitle file does not exist.
    """
    result = runner.invoke(app, [
        "merge",
        "--primary", "nonexistent.srt",
        "--secondary", str(SUB_PATH / "secondary.srt")
    ])
    assert result.exit_code == 1
    assert "Error in loading subtitles" in strip_ansi(result.output)

def test_invalid_primary_file_format() -> None:
    """
    Test error when the primary subtitle file format is invalid.
    """
    result = runner.invoke(app, [
        "merge",
        "--primary", str(SUB_PATH / "primary.txt"),
        "--secondary", str(SUB_PATH / "secondary.srt")
    ])
    assert result.exit_code == 1
    assert "Error in loading subtitles" in strip_ansi(result.output)

def test_empty_primary_file() -> None:
    """
    Test error when the primary subtitle file is empty.
    """
    primary_subs = str(SUB_PATH / "primary.ass")
    result = runner.invoke(app, [
        "merge",
        "--primary", primary_subs,
        "--secondary", str(SUB_PATH / "secondary.srt")
    ])
    assert result.exit_code == 1
    assert (
        f"Primary subtitle file '{primary_subs}' is empty." 
        in strip_ansi(result.output)
    )

# ------------------------
# Model / Device Error Tests
# ------------------------

def test_invalid_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Test error handling for invalid model name during loading.
    """
    def mock_load_model(*_args: Any, **_kwargs: Any) -> None:
        raise LoadModelError("Model not found")

    monkeypatch.setattr(
        "duosubs.core.merge_pipeline.load_sentence_transformer_model", mock_load_model
    )

    result = runner.invoke(app, [
        "merge",
        "--primary", str(SUB_PATH / "primary.srt"),
        "--secondary", str(SUB_PATH / "secondary.srt")
    ])
    assert result.exit_code == 2
    assert "Model not found" in strip_ansi(result.output)

# ------------------------
# Invalid Parameters Tests
# ------------------------

def test_invalid_device() -> None:
    """
    Test error for invalid device argument value.
    """
    result = runner.invoke(app, [
        "merge",
        "--primary", str(SUB_PATH / "primary.srt"),
        "--secondary", str(SUB_PATH / "secondary.srt"),
        "--device", "amd"
    ])
    assert result.exit_code != 0
    assert "Invalid value for '--device'" in strip_ansi(result.output)

def test_invalid_batch_size() -> None:
    """
    Test error for batch size below minimum allowed value.
    """
    result = runner.invoke(app, [
        "merge",
        "--primary", str(SUB_PATH / "primary.srt"),
        "--secondary", str(SUB_PATH / "secondary.srt"),
        "--batch-size", "-1"
    ])
    assert result.exit_code != 0
    assert "Invalid value for '--batch-size'" in strip_ansi(result.output)

def test_invalid_precision() -> None:
    """
    Test error for invalid precision argument.
    """
    result = runner.invoke(app, [
        "merge",
        "--primary", str(SUB_PATH / "primary.srt"),
        "--secondary", str(SUB_PATH / "secondary.srt"),
        "--model-precision", "float"
    ])
    assert result.exit_code != 0
    assert "Invalid value for '--model-precision'" in strip_ansi(result.output)

def test_invalid_omit() -> None:
    """
    Test error for invalid omit file type argument.
    """
    result = runner.invoke(app, [
        "merge",
        "--primary", str(SUB_PATH / "primary.srt"),
        "--secondary", str(SUB_PATH / "secondary.srt"),
        "--omit", "nothing"
    ])
    assert result.exit_code != 0
    assert "Invalid value for '--omit'" in strip_ansi(result.output)

@pytest.mark.parametrize("case", [
    "--format-all", 
    "--format-combined", 
    "--format-primary", 
    "--format-secondary"
])
def test_invalid_format(case: str) -> None:
    """
    Test error for invalid subtitle format argument value.

    Args:
        case (str): The CLI argument for subtitle format.
    """
    result = runner.invoke(app, [
        "merge",
        "--primary", str(SUB_PATH / "primary.srt"),
        "--secondary", str(SUB_PATH / "secondary.srt"),
        case, "txt"
    ])
    assert result.exit_code != 0
    assert f"Invalid value for '{case}'" in strip_ansi(result.output)

# ------------------------
# Print Help Tests
# ------------------------

def test_merge_help() -> None:
    """
    Test that the CLI help message is printed and contains key options.
    """
    result = runner.invoke(app, ["merge","--help"])
    assert result.exit_code == 0
    assert "--primary" in strip_ansi(result.output)
    assert "--secondary" in strip_ansi(result.output)

# ------------------------
# Functional Smoke Tests
# ------------------------

def test_successful_merge(tmp_path: Path) -> None:
    """
    Test a successful merge run and output zip file creation.

    Args:
        tmp_path (Path): Temporary directory for output files.
    """
    result = runner.invoke(app, [
        "merge",
        "--primary", str(SUB_PATH / "primary.srt"),
        "--secondary", str(SUB_PATH / "secondary.srt"),
        "--output-dir", str(tmp_path),
        "--model", "sentence-transformers/all-MiniLM-L6-v2"
    ])

    assert result.exit_code == 0
    assert any(p.suffix == ".zip" for p in tmp_path.iterdir())

# ------------------------
# Logger Output Tests
# ------------------------

def test_stage_logger_output(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Test that logger output from the pipeline is printed to the CLI output.
    """
    def mock_run_pipeline(
            _args: Any,
            logger: Callable[[str], None],
            *_args2: Any
        ) -> None:
        logger("Stage 1 log")
        logger("Stage 2 log")

    monkeypatch.setattr("duosubs.cli.main.run_merge_pipeline", mock_run_pipeline)

    result = runner.invoke(app, [
        "merge",
        "--primary", str(SUB_PATH / "primary.srt"),
        "--secondary", str(SUB_PATH / "secondary.srt")
    ])
    assert "Stage 1 log" in strip_ansi(result.output)
    assert "Stage 2 log" in strip_ansi(result.output)
