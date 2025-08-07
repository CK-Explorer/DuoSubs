
"""
Utility functions for formatting progress bars and numbers for monitoring UI.

These functions provide visual feedback for memory usage and other metrics in the web 
UI.
"""

def bar(percent: float, length: int = 12) -> str:
    """
    Returns a text progress bar representing a percentage.

    This function creates a string with filled and empty bar characters based on the 
    given percentage.

    Args:
        percent (float): The percentage to represent (0-100).
        length (int): The total length of the bar (number of characters).

    Returns:
        str: A string with filled and empty bar characters.
    """
    filled = int(percent / 100 * length)
    return "█" * filled + "░" * (length - filled)

def format_number(value: float, total_width: int = 6, precision: int = 2) -> str:
    """
    Formats a float value as a string with specified width and precision.

    This function ensures the formatted string has a total width and a specified number 
    of decimal places.

    Args:
        value (float): The float value to format.
        total_width (int): The total width of the formatted string.
        precision (int): Number of decimal places.

    Returns:
        str: The formatted number as a string.
    """
    return f"{value:>{total_width}.{precision}f}"

