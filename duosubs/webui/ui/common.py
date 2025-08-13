
"""
Utility functions for device detection, GPU listing, and HTML file reading for the web 
UI.

These functions help in determining available devices for model inference, listing GPU 
names, and reading HTML content for the UI.
"""

import platform
from pathlib import Path

import torch

from duosubs.common.enums import DeviceType


def open_html(file: str | Path) -> str:
    """
    Reads and returns the content of an HTML file.

    Args:
        file (str | Path): Path to the HTML file (str or Path).

    Returns:
        str: The content of the HTML file as a string.
    """
    content = ""
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()
    return content

def auto_filter_device() -> list[str]:
    """
    Returns a list of available device types for model inference.

    This function checks for CUDA, MPS (Metal Performance Shaders on macOS), and CPU 
    availability.

    Returns:
        list[str]: List of available device types (e.g., ['CUDA', 'MPS', 'CPU']).
    """
    available_device: list[str] = []

    if torch.cuda.is_available():
        available_device.append(DeviceType.CUDA.value)

    if torch.backends.mps.is_available() and platform.system() == "Darwin":
        available_device.append(DeviceType.MPS.value)

    available_device.append(DeviceType.CPU.value)

    return available_device

def auto_list_gpu_name() -> list[str]:
    """
    Returns a list of available GPU names, or ['N/A'] if no GPU is available.

    Returns:
        list[str]: List of GPU names or ['N/A'].
    """
    gpu_list = (
        [
            f"{torch.cuda.get_device_name(i)}" 
            for i in range(torch.cuda.device_count())
        ] if torch.cuda.is_available() else ["N/A"]
    )
    return gpu_list
