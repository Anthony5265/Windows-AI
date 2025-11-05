"""Utilities for computer vision tasks.

These utilities provide a minimal but functional pipeline for handling
vision-related operations. Images are preprocessed with :mod:`PIL`, tasks are
planned based on simple heuristics, and the execution layer can either process
data locally or forward it to remote APIs.
"""

from __future__ import annotations

from typing import Any, Dict, List

import base64
import io

try:  # Optional dependency
    import requests  # type: ignore
except Exception:  # pragma: no cover - graceful fallback
    requests = None  # type: ignore

try:  # Optional dependency
    from PIL import Image  # type: ignore
except Exception:  # pragma: no cover - graceful fallback
    Image = None  # type: ignore


def input_processor(image: Any) -> "Image.Image":
    """Prepare ``image`` data for model or API consumption.

    Parameters
    ----------
    image:
        Raw input which may be a :class:`~PIL.Image.Image`, a path to an
        image on disk, a file like object or raw ``bytes``. The function
        normalises the input into an RGB image with a fixed ``224x224`` size
        which is a common default for vision models.
    """

    if Image is None:
        raise RuntimeError("Pillow is required for image processing")

    if isinstance(image, Image.Image):
        img = image
    elif isinstance(image, (bytes, bytearray)):
        # Accept raw bytes so callers can read from network or database
        img = Image.open(io.BytesIO(image))
    else:  # Assume a file path or file-like object
        img = Image.open(image)

    img = img.convert("RGB")
    img = img.resize((224, 224))
    return img


def task_planner(processed_image: "Image.Image") -> Dict[str, Any]:
    """Plan the sequence of vision tasks to perform.

    The planner currently performs a very small amount of reasoning.  A local
    brightness calculation is always scheduled.  If the mean pixel value falls
    below ``dark_threshold`` a secondary remote classification task is also
    queued.

    Parameters
    ----------
    processed_image:
        Image that has already gone through :func:`input_processor`.
    dark_threshold:
        If the mean brightness is below this value a remote classification step
        will be included.  Defaults to ``100`` which roughly indicates a dark
        image.
    """

    if Image is None:
        raise RuntimeError("Pillow is required for image processing")

    gray = processed_image.convert("L")
    mean = sum(gray.getdata()) / (gray.width * gray.height)

    plan: List[Dict[str, Any]] = [
        {"type": "local", "operation": "brightness", "image": gray}
    ]

    if mean < dark_threshold:
        plan.append(
            {
                "type": "remote",
                "operation": "classify",
                "url": "https://api.example.com/vision",
                "image": processed_image,
                "timeout": 10,
            }
        )

    return {"plan": plan}


def executor(plan: Dict[str, Any]) -> Dict[str, Any]:
    """Execute vision tasks described in ``plan``.

    Local tasks are performed directly with :mod:`PIL`. Remote tasks are sent to
    a hypothetical API endpoint using :func:`requests.post`. Each executed step
    appends its output to the returned ``results`` list.  Network failures are
    captured and returned as error entries so the caller can decide how to
    handle them.
    """

    results: List[Dict[str, Any]] = []

    for step in plan.get("plan", []):
        if step.get("type") == "local" and step.get("operation") == "brightness":
            if Image is None:
                raise RuntimeError("Pillow is required for image processing")
            img: "Image.Image" = step["image"]
            mean = sum(img.getdata()) / (img.width * img.height)
            results.append({"brightness": mean})
        elif step.get("type") == "remote":
            if Image is None or requests is None:
                raise RuntimeError("Pillow and requests are required for remote vision tasks")
            img = step["image"]
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
            try:
                response = requests.post(
                    step["url"], json={"image": encoded}, timeout=step.get("timeout", 10)
                )
                response.raise_for_status()
                results.append(response.json())
            except requests.RequestException as exc:  # pragma: no cover - network error path
                results.append({"error": str(exc)})

    return {"results": results}


def result_aggregator(results: Dict[str, Any]) -> Dict[str, Any]:
    """Combine results from the executed vision tasks."""

    aggregated: Dict[str, Any] = {}
    for item in results.get("results", []):
        aggregated.update(item)
    return aggregated
