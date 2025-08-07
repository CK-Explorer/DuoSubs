
"""
Unit tests for bar and format_number utility functions in DuoSubs web UI monitor.
"""

import pytest

from duosubs.webui.monitor.common import bar, format_number


@pytest.mark.parametrize(
        "percent, length, output",
        [
            (0, 10, "░░░░░░░░░░"),
            (50, 10, "█████░░░░░"),
            (100, 10, "██████████")

        ]
    )
def test_bar(percent: float, length: int, output: str) -> None:
    """
    Test that bar() returns the correct progress bar string for given percent and 
    length.

    Args:
        percent (float): The percentage to represent (0-100).
        length (int): The total length of the bar.
        output (str): The expected output string.
    """
    assert bar(percent, length) == output

@pytest.mark.parametrize(
        "value, total_width, precision, output",
        [
            (0, 4, 3, "0.000"),
            (34.3, 4, 2, "34.30"),
            (102, 6, 1, " 102.0")
        ]
    )
def test_format_number(
    value: float,
    total_width: int,
    precision: int,
    output: str
) -> None:
    """
    Test that format_number() returns the correct formatted string for given value, 
    width, and precision.

    Args:
        value (float): The value to format.
        total_width (int): The total width of the formatted string.
        precision (int): Number of decimal places.
        output (str): The expected output string.
    """
    assert format_number(value, total_width, precision) == output

