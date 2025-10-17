"""Eco computing utilities for Windows-AI.

The :mod:`eco` package provides energy tracking, scheduling helpers and
report generation aimed at reducing power consumption.  The modules are
light‑weight and rely only on the Python standard library and optional
``psutil`` hooks when available.
"""

from .tracker import EnergyTracker
from .reports import generate_report
from .scheduler import EcoScheduler
from .monitor import EcoMonitor

__all__ = ["EnergyTracker", "EcoScheduler", "EcoMonitor", "generate_report"]
