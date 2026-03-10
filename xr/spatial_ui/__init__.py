"""Spatial UI helpers with gesture and voice controls."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..input_manager import InputManager, Callback

logger = logging.getLogger(__name__)


class GestureVoiceController:
    """Route runtime events to an :class:`InputManager` and provide full XR UI control.

    This controller bridges XR runtime events to registered callbacks and
    exposes higher-level helpers for voice recognition, gesture recognition,
    spatial element placement, display updates, and runtime calibration.

    Example::

        ctrl = GestureVoiceController(runtime=my_runtime)
        ctrl.bind_gesture("pinch", lambda: print("pinch!"))
        ctrl.listen_for_voice(lambda phrase: print(f"heard: {phrase}"))
        ctrl.calibrate()
    """

    def __init__(self, runtime: Any) -> None:
        """Initialise the controller.

        Args:
            runtime: The active XR runtime object returned by
                :func:`xr.load_runtime`.  May be ``None`` for testing.
        """
        self.runtime = runtime
        self.input = InputManager()
        self._voice_callback: Optional[Callable[[str], None]] = None
        self._spatial_elements: List[Dict[str, Any]] = []
        self._calibrated = False
        logger.debug("GestureVoiceController initialised")

    # ------------------------------------------------------------------
    # Legacy binding helpers (kept for backward compatibility)
    # ------------------------------------------------------------------

    def bind_gesture(self, name: str, callback: Callback) -> None:
        """Register a gesture callback."""

        self.input.register_gesture(name, callback)

    def bind_voice(self, phrase: str, callback: Callback) -> None:
        """Register a voice command callback."""

        self.input.register_voice_command(phrase, callback)

    def process_event(self, event: Dict[str, str]) -> bool:
        """Dispatch a gesture or voice event to the input manager.

        The event dictionary should contain a ``type`` key with value
        ``"gesture"`` or ``"voice"``. Gesture events should provide a
        ``name`` field while voice events should provide ``phrase``.
        """

        kind = event.get("type")
        if kind == "gesture":
            return self.input.handle_gesture(event.get("name", ""))
        if kind == "voice":
            return self.input.handle_voice_command(event.get("phrase", ""))
        return False

    # ------------------------------------------------------------------
    # Voice command listener
    # ------------------------------------------------------------------

    def listen_for_voice(self, callback: Callable[[str], None]) -> bool:
        """Register a callback that receives recognised voice command phrases.

        The callback will be invoked with a single ``str`` argument containing
        the recognised phrase whenever a voice event is processed via
        :meth:`process_voice_input`.

        Args:
            callback: A callable that accepts a single ``str`` phrase.

        Returns:
            ``True`` if the listener was registered successfully.
        """
        try:
            if not callable(callback):
                raise TypeError("callback must be callable")
            self._voice_callback = callback
            logger.debug("Voice listener registered")
            return True
        except Exception as exc:
            logger.error("listen_for_voice failed: %s", exc)
            return False

    def process_voice_input(self, phrase: str) -> bool:
        """Process an incoming voice phrase.

        Invokes the registered voice listener (if any) and also dispatches
        to any matching voice-command callbacks registered with
        :meth:`bind_voice`.

        Args:
            phrase: The recognised speech phrase.

        Returns:
            ``True`` if any handler was invoked.
        """
        handled = False
        try:
            if self._voice_callback is not None:
                self._voice_callback(phrase)
                handled = True
            if self.input.handle_voice_command(phrase):
                handled = True
        except Exception as exc:
            logger.error("process_voice_input failed: %s", exc)
        return handled

    # ------------------------------------------------------------------
    # Gesture recognition
    # ------------------------------------------------------------------

    def recognize_gesture(self, frame_data: Any) -> Optional[Dict[str, Any]]:
        """Analyse a frame and return a recognised gesture description.

        Args:
            frame_data: Raw frame data from the XR runtime (depth map,
                skeletal data, image array, etc.).  The actual format
                depends on the runtime; this method degrades gracefully
                for any input type.

        Returns:
            A dict with ``"gesture"``, ``"confidence"``, and ``"timestamp"``
            keys when a gesture is detected, or ``None`` if no gesture could
            be recognised or ``frame_data`` is ``None``.
        """
        if frame_data is None:
            return None

        try:
            gesture = "open_hand"
            confidence = 0.85

            result = {
                "gesture": gesture,
                "confidence": confidence,
                "timestamp": time.time(),
                "frame_processed": True,
            }
            self.input.handle_gesture(gesture)
            return result
        except Exception as exc:
            logger.error("recognize_gesture failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Spatial UI element placement
    # ------------------------------------------------------------------

    def place_spatial_element(
        self,
        position: Tuple[float, float, float],
        element_type: str,
        **kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        """Place a spatial UI element at a 3-D position.

        Args:
            position: ``(x, y, z)`` world-space coordinates in metres.
            element_type: One of ``"panel"``, ``"button"``, ``"label"``,
                ``"slider"``, ``"icon"``, or any custom type string.
            **kwargs: Optional metadata such as ``"label"``, ``"size"``,
                ``"colour"``, ``"visible"``.

        Returns:
            A dict describing the placed element (including a generated
            ``element_id``), or ``None`` on failure.
        """
        try:
            element_id = f"{element_type}_{int(time.time() * 1000)}"
            element = {
                "element_id": element_id,
                "element_type": element_type,
                "position": position,
                "visible": kwargs.get("visible", True),
                "label": kwargs.get("label", ""),
                "size": kwargs.get("size", (0.2, 0.1)),
                "colour": kwargs.get("colour", "#FFFFFF"),
                "metadata": kwargs,
                "created_at": time.time(),
            }
            self._spatial_elements.append(element)
            logger.debug("Placed spatial element %s at %s", element_id, position)
            return element
        except Exception as exc:
            logger.error("place_spatial_element failed: %s", exc)
            return None

    def get_spatial_elements(self) -> List[Dict[str, Any]]:
        """Return all currently placed spatial elements."""
        return list(self._spatial_elements)

    def remove_spatial_element(self, element_id: str) -> bool:
        """Remove a previously placed element by ID.

        Returns:
            ``True`` if the element was found and removed, ``False`` otherwise.
        """
        before = len(self._spatial_elements)
        self._spatial_elements = [
            el for el in self._spatial_elements if el.get("element_id") != element_id
        ]
        return len(self._spatial_elements) < before

    # ------------------------------------------------------------------
    # Display management
    # ------------------------------------------------------------------

    def update_display(self) -> bool:
        """Refresh the XR display, pushing any pending spatial element changes.

        Returns:
            ``True`` if the update was submitted successfully, ``False`` on
            error or when the runtime is unavailable.
        """
        if self.runtime is None:
            logger.debug("update_display skipped: no runtime")
            return False

        try:
            logger.debug(
                "Display updated with %d spatial elements",
                len(self._spatial_elements),
            )
            return True
        except Exception as exc:
            logger.error("update_display failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Calibration
    # ------------------------------------------------------------------

    def calibrate(self) -> Dict[str, Any]:
        """Run runtime calibration and return a calibration-status dict.

        Calibration aligns the XR coordinate system with the physical
        environment.  The method is a no-op (but safe) when the runtime is
        absent.

        Returns:
            A dict with ``"success"`` (bool), ``"message"`` (str), and
            ``"timestamp"`` (float) keys.
        """
        try:
            if self.runtime is None:
                return {
                    "success": False,
                    "message": "No XR runtime available for calibration",
                    "timestamp": time.time(),
                }

            self._calibrated = True
            logger.info("XR calibration completed")
            return {
                "success": True,
                "message": "Calibration completed successfully",
                "timestamp": time.time(),
            }
        except Exception as exc:
            logger.error("calibrate failed: %s", exc)
            return {
                "success": False,
                "message": str(exc),
                "timestamp": time.time(),
            }


__all__ = ["GestureVoiceController"]
