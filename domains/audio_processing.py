"""Utilities for audio processing tasks.

The functions below illustrate how audio-related operations might choose between
local processing and external API calls.
"""

from __future__ import annotations
from typing import Any, Dict, List


# Duration threshold (in seconds) beyond which processing is delegated to a
# remote API rather than handled locally.  The value is intentionally small for
# demonstration purposes.
REMOTE_THRESHOLD = 5.0


def input_processor(audio: Any) -> Dict[str, Any]:
    """Prepare ``audio`` data for downstream consumption.

    The function inspects ``audio`` and determines whether the data should be
    handled locally or sent to a remote API.  ``audio`` may be any object but
    tests primarily provide a dictionary with a ``duration`` field measured in
    seconds.  If ``duration`` exceeds :data:`REMOTE_THRESHOLD` the audio will be
    routed to a remote service.
    """

    if isinstance(audio, dict):
        duration = float(audio.get("duration", 0))
        data = audio.get("data")
    else:
        # Fallback: treat the length of the input as milliseconds and convert
        # to seconds.  This keeps the example functional for simple inputs like
        # byte strings while remaining light-weight.
        duration = len(audio) / 1000 if hasattr(audio, "__len__") else 0
        data = audio

    use_remote = duration > REMOTE_THRESHOLD
    return {"data": data, "duration": duration, "use_remote": use_remote}


def task_planner(processed_audio: Dict[str, Any]) -> Dict[str, Any]:
    """Determine the audio processing steps to execute.

    The planner creates a simple plan containing a single transcription step
    and records whether the step should be executed locally or remotely based on
    the ``use_remote`` flag provided by :func:`input_processor`.
    """

    step = {
        "type": "transcribe",
        "mode": "remote" if processed_audio.get("use_remote") else "local",
        "audio": processed_audio.get("data"),
    }
    return {"steps": [step]}


def executor(plan: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the planned audio processing steps."""

    results: List[Dict[str, Any]] = []
    for step in plan.get("steps", []):
        mode = step.get("mode", "local")
        audio = step.get("audio")
        output = _local_transcribe(audio) if mode == "local" else _call_remote_api(audio)
        results.append({"type": step.get("type"), "mode": mode, "output": output})

    return {"results": results}


def result_aggregator(results: Dict[str, Any]) -> Dict[str, Any]:
    """Merge outputs from audio processing tasks."""

    items = results.get("results", [])
    transcripts = [item.get("output", "") for item in items]
    modes = [item.get("mode") for item in items]
    return {"transcript": " ".join(transcripts).strip(), "modes": modes}


def _local_transcribe(audio: Any) -> str:
    """Placeholder implementation of a local transcription model."""

    # A realistic implementation would load and run an on-device model.  We keep
    # the example light-weight and deterministic for testing.
    return "local transcript"


def _call_remote_api(audio: Any) -> str:
    """Placeholder that simulates a remote transcription API call."""

    # The real function would send ``audio`` to a remote service using HTTP
    # requests.  Importing ``requests`` here keeps the dependency optional until
    # remote execution is actually attempted.
    import requests  # type: ignore

    payload = {"audio": str(audio)}
    response = requests.post(
        "https://example.com/api/transcribe", json=payload, timeout=10
    )
    response.raise_for_status()
    data = response.json()
    return data.get("transcription", "")
