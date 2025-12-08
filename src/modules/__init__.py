"""Init-fil for modules-pakken.

This module exposes a small set of public symbols but defers importing
the heavy submodules (GUI, plotting, etc.) until the attribute is
actually accessed. That keeps a plain ``import modules`` safe in
headless CI or environments without optional dependencies.
"""

# Public API names -> corresponding submodule filenames
__all__ = ["ZeroShiftCalculator", "RifleOpticManager", "InventoryManager"]

_name_to_mod = {
    "InventoryManager": "inventory_manager",
    "RifleOpticManager": "rifle_optic_manager",
    "ZeroShiftCalculator": "zero_shift_calculator",
}


def __getattr__(name: str):
    """Lazily import and return a public symbol from its submodule.

    Called when an attribute lookup on the package fails. This avoids
    importing GUI-related dependencies at package import time.
    """
    if name in _name_to_mod:
        from importlib import import_module

        try:
            mod = import_module(f".{_name_to_mod[name]}", __name__)
        except Exception as exc:  # pragma: no cover - runtime guard
            raise ImportError(
                f"Optional dependency required to access '{name}'. "
                f"Importing its submodule failed: {exc}.\n"
                "Install the optional requirements or import the submodule "
                "directly (e.g. 'from modules import inventory_manager')"
            ) from exc

        value = getattr(mod, name)
        globals()[name] = value
        return value
    raise AttributeError(name)


def __dir__():
    return sorted(list(globals().keys()) + __all__)
