"""XR Spatial UI Panel – floating panel elements in extended-reality space.

A :class:`SpatialPanel` represents a rectangular UI surface that can be
positioned, shown, hidden, and updated at runtime.  Panels are designed to
work with any XR runtime; when no runtime is present all methods degrade
gracefully.

Typical usage::

    from xr.spatial_ui.panel import SpatialPanel

    panel = SpatialPanel(panel_id="hud", runtime=my_runtime)
    panel.create(size=(0.4, 0.3))
    panel.set_position((0.0, 1.6, -0.5))
    panel.update_content({"title": "Hello XR", "body": "Welcome"})
    panel.show()
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SpatialPanel:
    """A floating rectangular UI panel rendered in XR world-space.

    Attributes:
        panel_id: Unique identifier for this panel.
        runtime: The XR runtime object (may be ``None``).

    Example::

        panel = SpatialPanel("info_panel", runtime=None)
        panel.create()
        panel.update_content({"text": "Hello!"})
        panel.show()
    """

    def __init__(
        self,
        panel_id: str,
        runtime: Optional[Any] = None,
    ) -> None:
        """Initialise the spatial panel.

        Args:
            panel_id: A unique string identifier for this panel.
            runtime: The XR runtime object, or ``None`` for offline mode.
        """
        self.panel_id = panel_id
        self.runtime = runtime

        self._created = False
        self._visible = False
        self._position: Tuple[float, float, float] = (0.0, 1.5, -0.5)
        self._orientation: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)
        self._size: Tuple[float, float] = (0.3, 0.2)
        self._content: Dict[str, Any] = {}
        self._children: List[Dict[str, Any]] = []
        self._style: Dict[str, Any] = {
            "background_colour": "#1E1E2E",
            "border_colour": "#7C7CFF",
            "border_width": 0.002,
            "corner_radius": 0.01,
            "opacity": 0.95,
            "font_size": 0.02,
            "font_colour": "#FFFFFF",
        }

        logger.debug("SpatialPanel '%s' initialised", panel_id)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def create(
        self,
        size: Optional[Tuple[float, float]] = None,
        style: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Allocate the panel in the XR scene graph.

        Args:
            size: Optional ``(width, height)`` in metres.  Defaults to
                ``(0.3, 0.2)`` if not supplied.
            style: Optional style overrides (merged with defaults).

        Returns:
            ``True`` if the panel was created successfully.
        """
        try:
            if size is not None:
                self._size = (float(size[0]), float(size[1]))
            if style is not None:
                self._style.update(style)

            self._created = True
            self._visible = False
            logger.debug(
                "SpatialPanel '%s' created (size=%s)", self.panel_id, self._size
            )
            return True
        except Exception as exc:
            logger.error("SpatialPanel.create failed: %s", exc)
            return False

    def destroy(self) -> bool:
        """Remove the panel from the XR scene graph.

        Returns:
            ``True`` if successfully destroyed (or was not created).
        """
        try:
            self._created = False
            self._visible = False
            self._children.clear()
            logger.debug("SpatialPanel '%s' destroyed", self.panel_id)
            return True
        except Exception as exc:
            logger.error("SpatialPanel.destroy failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Visibility
    # ------------------------------------------------------------------

    def show(self) -> bool:
        """Make the panel visible in the XR scene.

        Returns:
            ``True`` on success.  Returns ``False`` if the panel has not
            been created yet.
        """
        if not self._created:
            logger.warning(
                "SpatialPanel.show called before create on panel '%s'",
                self.panel_id,
            )
            return False

        try:
            self._visible = True
            logger.debug("SpatialPanel '%s' shown", self.panel_id)
            return True
        except Exception as exc:
            logger.error("SpatialPanel.show failed: %s", exc)
            return False

    def hide(self) -> bool:
        """Hide the panel without destroying its resources.

        Returns:
            ``True`` on success.
        """
        try:
            self._visible = False
            logger.debug("SpatialPanel '%s' hidden", self.panel_id)
            return True
        except Exception as exc:
            logger.error("SpatialPanel.hide failed: %s", exc)
            return False

    @property
    def is_visible(self) -> bool:
        """``True`` if the panel is currently visible."""
        return self._created and self._visible

    # ------------------------------------------------------------------
    # Content management
    # ------------------------------------------------------------------

    def update_content(self, content: Dict[str, Any]) -> bool:
        """Replace the panel's content dictionary and trigger a redraw.

        Args:
            content: Arbitrary key-value pairs describing the panel
                content.  Common keys: ``"title"``, ``"body"``,
                ``"image_url"``, ``"progress"``.

        Returns:
            ``True`` on success.
        """
        try:
            self._content = dict(content)
            self._content["_updated_at"] = time.time()
            logger.debug(
                "SpatialPanel '%s' content updated: keys=%s",
                self.panel_id,
                list(content.keys()),
            )
            return True
        except Exception as exc:
            logger.error("SpatialPanel.update_content failed: %s", exc)
            return False

    def get_content(self) -> Dict[str, Any]:
        """Return the current content dictionary (a shallow copy)."""
        return dict(self._content)

    def add_child(
        self,
        child_id: str,
        child_type: str,
        relative_position: Tuple[float, float] = (0.0, 0.0),
        **kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        """Add a child UI element to the panel.

        Args:
            child_id: Unique identifier for the child within this panel.
            child_type: Element type (``"button"``, ``"label"``, ``"icon"``…).
            relative_position: ``(x, y)`` offset from the panel centre.
            **kwargs: Additional element properties.

        Returns:
            The child descriptor dict, or ``None`` on failure.
        """
        try:
            child = {
                "child_id": child_id,
                "child_type": child_type,
                "relative_position": relative_position,
                "created_at": time.time(),
                **kwargs,
            }
            self._children = [c for c in self._children if c["child_id"] != child_id]
            self._children.append(child)
            return child
        except Exception as exc:
            logger.error("SpatialPanel.add_child failed: %s", exc)
            return None

    def remove_child(self, child_id: str) -> bool:
        """Remove a child element by ID.

        Returns:
            ``True`` if the child was found and removed.
        """
        before = len(self._children)
        self._children = [c for c in self._children if c["child_id"] != child_id]
        return len(self._children) < before

    # ------------------------------------------------------------------
    # Transform
    # ------------------------------------------------------------------

    def set_position(
        self,
        position: Tuple[float, float, float],
        orientation: Optional[Tuple[float, float, float, float]] = None,
    ) -> bool:
        """Set the panel's world-space position (and optionally orientation).

        Args:
            position: ``(x, y, z)`` world-space coordinates in metres.
            orientation: Optional ``(qx, qy, qz, qw)`` quaternion.  The
                current orientation is preserved when ``None``.

        Returns:
            ``True`` on success.
        """
        try:
            self._position = (float(position[0]), float(position[1]), float(position[2]))
            if orientation is not None:
                self._orientation = (
                    float(orientation[0]),
                    float(orientation[1]),
                    float(orientation[2]),
                    float(orientation[3]),
                )
            logger.debug(
                "SpatialPanel '%s' moved to %s", self.panel_id, self._position
            )
            return True
        except Exception as exc:
            logger.error("SpatialPanel.set_position failed: %s", exc)
            return False

    def get_position(self) -> Tuple[float, float, float]:
        """Return the current world-space position."""
        return self._position

    def get_orientation(self) -> Tuple[float, float, float, float]:
        """Return the current orientation quaternion ``(qx, qy, qz, qw)``."""
        return self._orientation

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the panel state to a plain dictionary."""
        return {
            "panel_id": self.panel_id,
            "created": self._created,
            "visible": self._visible,
            "position": self._position,
            "orientation": self._orientation,
            "size": self._size,
            "content": dict(self._content),
            "children": list(self._children),
            "style": dict(self._style),
        }

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"SpatialPanel(panel_id={self.panel_id!r}, "
            f"visible={self._visible}, "
            f"position={self._position})"
        )


__all__ = ["SpatialPanel"]
