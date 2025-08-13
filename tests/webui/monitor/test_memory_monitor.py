"""
Unit tests for the LiveMemoryMonitor class, focusing on the memory status table 
generation.

Tests the integration of system RAM and GPU VRAM statistics, including correct 
formatting and bar visualization.
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from duosubs.webui.monitor.common import bar, format_number
from duosubs.webui.monitor.memory_monitor import LiveMemoryMonitor


@pytest.mark.parametrize(
        "ram, vram",
        [
            (
                (0, 0, 8e9),
                ("gpu1", 43.75, 7e9, 16e9)
            ),
            (
                (100, 32e9, 32e9),
                ("gpu2", 0, 0, 16e9)
            )
        ]
    )
def test_get_memory_status_table(
    ram: tuple[float, int, int],
    vram: tuple[str, float, int, int]
) -> None:
    """
    Test LiveMemoryMonitor._get_memory_status_table for correct DataFrame output.

    Args:
        ram (tuple[float, int, int]): System RAM stats as (percent, used, total).
        vram (tuple[str, float, int, int]): GPU VRAM stats as (name, percent, used, 
            total).
    """
    LiveMemoryMonitor._instance = None

    with patch(
            "duosubs.webui.monitor.memory_monitor.torch.cuda.is_available",
            return_value=True
        ), \
        patch(
            "duosubs.webui.monitor.memory_monitor.pynvml.nvmlDeviceGetCount",
            return_value=1
        ), \
        patch(
            "duosubs.webui.monitor.memory_monitor.psutil.virtual_memory"
        ) as mock_virtual_memory, \
        patch(
            "duosubs.webui.monitor.memory_monitor.pynvml.nvmlDeviceGetHandleByIndex"
        ) as mock_get_handle, \
        patch(
            "duosubs.webui.monitor.memory_monitor.pynvml.nvmlDeviceGetName"
        ) as mock_get_name, \
        patch(
            "duosubs.webui.monitor.memory_monitor.pynvml.nvmlDeviceGetMemoryInfo"
        ) as mock_get_mem_info:

        monitor = LiveMemoryMonitor()

        mock_virtual_memory.return_value = MagicMock(
            percent=ram[0],
            used=ram[1],
            total=ram[2]
        )

        mock_handle = MagicMock()
        mock_get_handle.return_value = mock_handle
        mock_get_name.return_value = vram[0]
        mock_get_mem_info.return_value = MagicMock(
            used=vram[2],
            total=vram[3]
        )

        df = monitor._get_memory_status_table()
        gib = 1024**3

        assert isinstance(df, pd.DataFrame)
        assert df.shape[0] == 2

        assert df.iloc[0]["Name"] == "💻 System RAM"
        assert df.iloc[0]["Usage"] == f"{bar(ram[0])}  {format_number(ram[0])}%"
        assert df.iloc[0]["Used"] ==  f"{format_number(ram[1] / gib)} GB"
        assert df.iloc[0]["Total"] == f"{format_number(ram[2] / gib)} GB"

        assert df.iloc[1]["Name"] == f"🚀 {vram[0]}"
        assert df.iloc[1]["Usage"] == f"{bar(vram[1])}  {format_number(vram[1])}%"
        assert df.iloc[1]["Used"] ==  f"{format_number(vram[2] / gib)} GB"
        assert df.iloc[1]["Total"] == f"{format_number(vram[3] / gib)} GB"
