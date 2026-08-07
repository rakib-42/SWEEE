"""Adapter around the project's existing ESP32 OLED display functions.

This module does NOT implement the OLED driver — that already exists
elsewhere in the project. It gives the speech pipeline a single,
stable call site (`set_state`) so listener.py / tts.py don't need to
know where the real display code lives.

Wire the import below to whatever the project already exposes (a
function that sends a state string to the ESP32's display, however
that's implemented). Until it's wired, state changes are just printed,
so nothing breaks if this module is dropped in before the real driver
is connected.
"""

from typing import Callable, Optional

_set_state: Optional[Callable[[str], None]] = None

# TODO: point this at the project's real OLED update function, e.g.:
#   from display import set_state as _set_state
#   from esp32_display import show_state as _set_state
try:
    from display import set_state as _set_state  # type: ignore
except ImportError:
    _set_state = None


def set_state(state: str) -> None:
    """Update the OLED display state. Falls back to a no-op if unwired."""
    if _set_state is not None:
        _set_state(state)