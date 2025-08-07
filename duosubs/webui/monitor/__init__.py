"""
Provides the LiveMemoryMonitor singleton for real-time system and GPU memory monitoring.

Attributes:
    live_memory_monitor: Singleton instance of LiveMemoryMonitor.
"""
from .memory_monitor import LiveMemoryMonitor

live_memory_monitor = LiveMemoryMonitor()
