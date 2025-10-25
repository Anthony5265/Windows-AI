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

    The function ensures the input is a :class:`~PIL.Image.Image`, converts it
    to RGB, and resizes it to ``224x224`` pixels.
    """

    if Image is None:
        raise RuntimeError("Pillow is required for image processing")

    if isinstance(image, Image.Image):
        img = image
    else:  # Assume a file path or file-like object
        img = Image.open(image)
    img = img.convert("RGB")
    img = img.resize((224, 224))
    return img


def task_planner(processed_image: "Image.Image") -> Dict[str, Any]:
    """Plan the sequence of vision tasks to perform.

    A very small planner that always includes a local brightness analysis. If
    the image is fairly dark (mean pixel value below ``100``), an additional
    remote classification step is scheduled.
    """

    if Image is None:
        raise RuntimeError("Pillow is required for image processing")

    gray = processed_image.convert("L")
    mean = sum(gray.getdata()) / (gray.width * gray.height)

    plan: List[Dict[str, Any]] = [
        {"type": "local", "operation": "brightness", "image": gray}
    ]

    if mean < 100:  # Arbitrary heuristic for demonstration purposes
        plan.append(
            {
                "type": "remote",
                "operation": "classify",
                "url": "https://api.example.com/vision",
                "image": processed_image,
            }
        )

    return {"plan": plan}


def executor(plan: Dict[str, Any]) -> Dict[str, Any]:
    """Execute vision tasks described in ``plan``.

    Local tasks are performed directly with :mod:`PIL`. Remote tasks are sent to
    a hypothetical API endpoint using :func:`requests.post`. Each executed step
    appends its output to the returned ``results`` list.
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
            response = requests.post(step["url"], json={"image": encoded})
            response.raise_for_status()
            results.append(response.json())

    return {"results": results}


def result_aggregator(results: Dict[str, Any]) -> Dict[str, Any]:
    """Combine results from the executed vision tasks."""

    aggregated: Dict[str, Any] = {}
    for item in results.get("results", []):
        aggregated.update(item)
    return aggregated
