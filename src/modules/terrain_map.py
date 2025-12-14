"""Shim module that re-exports the canonical terrain_map baseline.

This avoids duplicated definitions while preserving the original
module path `src.modules.terrain_map`. Editors, tests and importers
can import this file safely; the real implementation lives in
`src.modules.terrain_map_baseline`.
"""

from src.modules.terrain_map_baseline import *  # noqa: F401,F403

__all__ = getattr(
    __import__("src.modules.terrain_map_baseline", fromlist=["__all__"]), "__all__", []
)
