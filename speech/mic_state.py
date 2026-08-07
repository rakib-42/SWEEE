"""Shared microphone lock / cooldown state for the speech pipeline.

Speaking and cooldown are represented as a flag and a timestamp that the
frame loop checks on every incoming packet, rather than sleeping the
whole process. That keeps the UDP socket continuously drained (so the
ESP32 never backs up or times out) while audio is simply ignored
instead of processed.
"""

import time
from typing import Optional

from speech.config import COOLDOWN_SECONDS

MIC_ENABLED: bool = True
_cooldown_until: Optional[float] = None


def lock_microphone() -> None:
    """Disable the microphone. Call this before any speech/reaction audio plays."""
    global MIC_ENABLED
    MIC_ENABLED = False


def unlock_microphone_and_start_cooldown(cooldown: bool = True) -> None:
    """Re-enable the microphone after speech finishes.

    If `cooldown` is True, a COOLDOWN_SECONDS window starts during which
    incoming audio is still ignored (used after the AI's spoken reply).
    Pass `cooldown=False` for cases like the "Yes?" confirmation, where
    Command Mode should start listening immediately.
    """
    global MIC_ENABLED, _cooldown_until
    MIC_ENABLED = True
    _cooldown_until = time.monotonic() + COOLDOWN_SECONDS if cooldown else None


def in_cooldown() -> bool:
    """True while the post-speech cooldown window is still active."""
    return _cooldown_until is not None and time.monotonic() < _cooldown_until


def is_audio_accepted() -> bool:
    """True only when the mic is enabled and we're outside any cooldown window."""
    return MIC_ENABLED and not in_cooldown()