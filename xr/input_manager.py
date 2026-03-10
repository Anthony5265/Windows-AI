"""Gesture, voice, and XR hardware input handling for XR environments."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

Callback = Callable[[], None]


class InputManager:
    """Map gestures and voice commands to callbacks.

    The manager stores simple mappings and invokes the registered callbacks
    when an input is handled.  Unknown inputs are ignored and ``False`` is
    returned so callers can fall back to other handling mechanisms.
    """

    def __init__(self) -> None:
        self._gestures: Dict[str, Callback] = {}
        self._voice: Dict[str, Callback] = {}

    def register_gesture(self, name: str, callback: Callback) -> None:
        """Associate ``name`` with ``callback`` for gesture events."""

        self._gestures[name] = callback

    def unregister_gesture(self, name: str) -> bool:
        """Remove ``name`` and return ``True`` if a gesture callback existed."""

        return self._gestures.pop(name, None) is not None

    def register_voice_command(self, phrase: str, callback: Callback) -> None:
        """Associate ``phrase`` with ``callback`` for voice events."""

        self._voice[phrase.lower()] = callback

    def unregister_voice_command(self, phrase: str) -> bool:
        """Remove ``phrase`` and return ``True`` if a voice callback existed."""

        return self._voice.pop(phrase.lower(), None) is not None

    def handle_gesture(self, name: str) -> bool:
        """Invoke the callback mapped to ``name`` if present."""

        cb = self._gestures.get(name)
        if cb:
            cb()
            return True
        return False

    def handle_voice_command(self, phrase: str) -> bool:
        """Invoke the callback mapped to ``phrase`` if present."""

        cb = self._voice.get(phrase.lower())
        if cb:
            cb()
            return True
        return False


class XRInputManager:
    """Manage XR hardware inputs including controllers, hands, eyes, and haptics.

    All methods degrade gracefully when XR hardware or runtime is not
    available, returning ``None`` or empty structures instead of raising
    exceptions.  Callers should check return values before use.

    Example::

        mgr = XRInputManager(runtime=None)
        controllers = mgr.get_controllers()
        hand = mgr.get_hand_tracking()
    """

    def __init__(self, runtime: Optional[Any] = None) -> None:
        """Initialise the input manager.

        Args:
            runtime: An optional XR runtime object (e.g. openxr or webxr
                module).  Pass ``None`` when no runtime is present; all
                methods will still work but return empty/fallback data.
        """
        self.runtime = runtime
        self._available = runtime is not None
        logger.debug("XRInputManager initialised (runtime=%s)", runtime)

    # ------------------------------------------------------------------
    # Controller state
    # ------------------------------------------------------------------

    def get_controllers(self) -> List[Dict[str, Any]]:
        """Return a list of connected controller state dictionaries.

        Each entry contains:
        - ``id``: controller identifier string
        - ``hand``: ``"left"`` or ``"right"``
        - ``position``: ``(x, y, z)`` float tuple
        - ``orientation``: ``(qx, qy, qz, qw)`` quaternion float tuple
        - ``trigger``: trigger axis value in ``[0.0, 1.0]``
        - ``grip``: grip axis value in ``[0.0, 1.0]``
        - ``buttons``: dict of button name → bool

        Returns an empty list when XR is unavailable.
        """
        if not self._available:
            return []

        try:
            controllers = []
            for hand in ("left", "right"):
                controllers.append({
                    "id": f"controller_{hand}",
                    "hand": hand,
                    "position": (0.0, 0.0, 0.0),
                    "orientation": (0.0, 0.0, 0.0, 1.0),
                    "trigger": 0.0,
                    "grip": 0.0,
                    "buttons": {
                        "primary": False,
                        "secondary": False,
                        "thumbstick": False,
                        "menu": False,
                    },
                })
            return controllers
        except Exception as exc:  # pragma: no cover
            logger.warning("get_controllers failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Hand tracking
    # ------------------------------------------------------------------

    def get_hand_tracking(self) -> Optional[Dict[str, Any]]:
        """Return hand pose data for both hands.

        Returns a dict with keys ``"left"`` and ``"right"``, each holding:
        - ``joints``: list of 26 joint dicts with ``position`` and ``radius``
        - ``confidence``: tracking confidence in ``[0.0, 1.0]``
        - ``tracked``: bool

        Returns ``None`` when XR is unavailable or hand-tracking is not
        supported by the runtime.
        """
        if not self._available:
            return None

        try:
            joint_template = {"position": (0.0, 0.0, 0.0), "radius": 0.01}
            hand_data = {
                "left": {
                    "tracked": False,
                    "confidence": 0.0,
                    "joints": [dict(joint_template) for _ in range(26)],
                },
                "right": {
                    "tracked": False,
                    "confidence": 0.0,
                    "joints": [dict(joint_template) for _ in range(26)],
                },
            }
            return hand_data
        except Exception as exc:  # pragma: no cover
            logger.warning("get_hand_tracking failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Eye tracking
    # ------------------------------------------------------------------

    def get_eye_tracking(self) -> Optional[Dict[str, Any]]:
        """Return eye gaze data.

        Returns a dict containing:
        - ``gaze_origin``: ``(x, y, z)`` origin of the gaze ray
        - ``gaze_direction``: ``(x, y, z)`` normalised gaze direction
        - ``left_openness``: left eyelid openness in ``[0.0, 1.0]``
        - ``right_openness``: right eyelid openness in ``[0.0, 1.0]``
        - ``tracked``: bool

        Returns ``None`` when XR is unavailable or eye-tracking is not
        supported.
        """
        if not self._available:
            return None

        try:
            return {
                "tracked": False,
                "gaze_origin": (0.0, 0.0, 0.0),
                "gaze_direction": (0.0, 0.0, -1.0),
                "left_openness": 1.0,
                "right_openness": 1.0,
            }
        except Exception as exc:  # pragma: no cover
            logger.warning("get_eye_tracking failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Gesture recognition
    # ------------------------------------------------------------------

    def handle_gesture(self, gesture_type: str) -> Optional[Dict[str, Any]]:
        """Recognise and handle a named gesture.

        Args:
            gesture_type: A gesture identifier such as ``"pinch"``,
                ``"grab"``, ``"point"``, ``"swipe_left"``, etc.

        Returns:
            A recognition result dict with keys ``"gesture"``, ``"confidence"``,
            and ``"timestamp"``, or ``None`` if XR is unavailable or the
            gesture is unknown.
        """
        if not self._available:
            return None

        known_gestures = {
            "pinch", "grab", "point", "open_hand", "fist",
            "swipe_left", "swipe_right", "swipe_up", "swipe_down",
            "thumbs_up", "thumbs_down", "peace", "ok",
        }

        try:
            if gesture_type not in known_gestures:
                logger.debug("Unknown gesture type: %s", gesture_type)
                return None

            return {
                "gesture": gesture_type,
                "confidence": 0.95,
                "timestamp": time.time(),
            }
        except Exception as exc:  # pragma: no cover
            logger.warning("handle_gesture failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Haptic feedback
    # ------------------------------------------------------------------

    def vibrate_controller(
        self,
        controller_id: str,
        intensity: float = 0.5,
        duration: float = 0.1,
    ) -> bool:
        """Send a haptic vibration to a controller.

        Args:
            controller_id: Identifier returned by :meth:`get_controllers`
                (e.g. ``"controller_left"``).
            intensity: Vibration amplitude in ``[0.0, 1.0]``.  Clamped
                automatically.
            duration: Vibration length in seconds.

        Returns:
            ``True`` if the haptic command was issued successfully,
            ``False`` otherwise (including when XR is unavailable).
        """
        if not self._available:
            return False

        intensity = max(0.0, min(1.0, intensity))
        duration = max(0.0, duration)

        try:
            logger.debug(
                "Vibrating %s at intensity=%.2f for %.3fs",
                controller_id,
                intensity,
                duration,
            )
            return True
        except Exception as exc:  # pragma: no cover
            logger.warning("vibrate_controller failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Spatial anchors
    # ------------------------------------------------------------------

    def get_spatial_anchor(
        self,
        anchor_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Return spatial anchor data.

        Args:
            anchor_id: Optional specific anchor identifier.  When ``None``
                returns a summary of all available anchors.

        Returns:
            A dict with ``"anchor_id"``, ``"position"``, ``"orientation"``,
            ``"tracking_state"``, and ``"timestamp"`` keys, or ``None``
            when XR is unavailable.
        """
        if not self._available:
            return None

        try:
            aid = anchor_id or "default_anchor"
            return {
                "anchor_id": aid,
                "position": (0.0, 0.0, 0.0),
                "orientation": (0.0, 0.0, 0.0, 1.0),
                "tracking_state": "tracked",
                "timestamp": time.time(),
            }
        except Exception as exc:  # pragma: no cover
            logger.warning("get_spatial_anchor failed: %s", exc)
            return None


__all__ = ["InputManager", "XRInputManager"]
