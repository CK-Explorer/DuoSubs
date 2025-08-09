
"""
Provides LiveMemoryMonitor for real-time system and GPU memory usage reporting.

This module monitors system RAM and GPU VRAM usage, providing a live status table.
"""

import time
from typing import Iterator

import pandas as pd
import psutil
import pynvml  # type: ignore
import torch

from .common import bar, format_number


class LiveMemoryMonitor:
    """
    Singleton class for monitoring system RAM and GPU VRAM usage in real time.

    Attributes:
        _instance: Singleton instance.
        _has_cuda: Whether CUDA GPUs are available.
        _gpu_count: Number of detected GPUs.
    """
    _instance = None

    def __new__(cls) -> "LiveMemoryMonitor":
        """
        Returns the singleton instance of LiveMemoryMonitor.

        Returns:
            LiveMemoryMonitor: The singleton instance.
        """
        if cls._instance is None:
            cls._instance = super(LiveMemoryMonitor, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """
        Initializes the LiveMemoryMonitor, detects CUDA and GPU count.
        """
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._has_cuda = torch.cuda.is_available()
            self._gpu_count = 0

            if self._has_cuda:
                try:
                    pynvml.nvmlInit()
                    self._gpu_count = pynvml.nvmlDeviceGetCount()
                except Exception as e:
                    print(
                        f"[Warning] CUDA available but failed to initialize NVML: {e}"
                    )
                    self._has_cuda = False

    def auto_refresh(self) -> Iterator[pd.DataFrame]:
        """
        Generator that yields memory status tables every 3 seconds.

        Yields:
            pd.DataFrame: Table of current RAM and VRAM usage.
        """
        while True:
            yield self._get_memory_status_table()
            time.sleep(3)

    def _get_memory_status_table(self) -> pd.DataFrame:
        """
        Collects current system RAM and GPU VRAM usage into a DataFrame.

        Returns:
            pd.DataFrame: Table with columns [Name, Usage, Used, Total].
        """
        mem = psutil.virtual_memory()
        gib = 1024 ** 3
        ram_percent = mem.percent
        ram_row = [
            "💻 System RAM",
            f"{bar(ram_percent)}  {format_number(ram_percent)}%",
            f"{format_number(mem.used / gib)} GB",
            f"{format_number(mem.total / gib)} GB",
        ]

        rows = [ram_row]

        if self._has_cuda:
            for i in range(self._gpu_count):
                try:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    name = pynvml.nvmlDeviceGetName(handle)
                    mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    vram_percent = mem_info.used / mem_info.total * 100

                    rows.append([
                        f"🚀 {name}",
                        f"{bar(vram_percent)}  {format_number(vram_percent)}%",
                        f"{format_number(mem_info.used / gib)} GB",
                        f"{format_number(mem_info.total / gib)} GB"
                    ])
                except Exception as e:
                    rows.append(["N/A", "Not available", "N/A", "N/A"])
                    print(str(e))

        return pd.DataFrame(rows, columns=["Name", "Usage", "Used", "Total"])
