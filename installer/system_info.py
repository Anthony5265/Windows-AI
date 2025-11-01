"""Utility functions for detecting system information.

This module re-exports :func:`windows_ai.system_info_core.detect_system` to
avoid code duplication between the installer and the ``windows_ai`` package.
"""
from __future__ import annotations

from windows_ai.system_info_core import detect_system

__all__ = ["detect_system"]
