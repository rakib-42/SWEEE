"""Thin wrapper around the project's existing Piper TTS pipeline.

This does NOT reimplement or modify Piper. It only adds the
microphone-lock / cooldown / OLED bookkeeping that has to happen
around every spoken response, so Whisper and Silero never see the
robot's own voice (Requirement 7) and the mic stays disabled for the
right window afterward.

Any code that currently calls Piper directly (e.g. in app.py, to speak
the AI's reply) should call `speech.tts.speak()` instead so mic-lock
and cooldown are applied consistently. That is the one integration
point outside speech/ this feature needs.
"""

from typing import Callable, Optional

from speech import mic_state, oled

_piper_speak: Optional[Callable[[str], None]] = None

# TODO: point this at the project's real Piper call, e.g.:
#   from tts.piper import speak as _piper_speak
#   from piper_tts import synthesize_and_play as _piper_speak
try:
    from tts.piper import speak as _piper_speak  # type: ignore
except ImportError:
    _piper_speak = None


def speak(text: str, cooldown: bool = True) -> None:
    """Speak `text` through Piper with the microphone locked for the duration.

    `cooldown=True` (default) starts the post-speech cooldown window
    afterward — use this for the AI's spoken reply. `cooldown=False`
    unlocks the mic immediately with no cooldown — use this for the
    "Yes?" wake confirmation, where Command Mode should start listening
    right away.
    """
    mic_state.lock_microphone()
    oled.set_state("Speaking...")
    print("🔊 Speaking...")

    if _piper_speak is not None:
        _piper_speak(text)
    else:
        # Piper isn't wired into this environment; make the gap visible
        # instead of silently pretending speech happened.
        print(f"[Piper not wired] Would speak: {text}")

    mic_state.unlock_microphone_and_start_cooldown(cooldown=cooldown)

    if cooldown:
        oled.set_state("Cooldown...")
        print("⏳ Cooldown...")