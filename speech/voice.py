"""Piper text-to-speech: speaks the AI's replies out loud.

Loads a Piper voice once at import time and synthesizes arbitrary text
to a temporary WAV file, then plays it back the same way speech/sound.py
plays its canned clips (via playsound, in a background thread), so the
main app loop is never blocked.

The microphone is locked for the full duration of playback via the same
esp32.display.speaking() hook the rest of the pipeline already uses, and
a cooldown starts only once playback actually finishes — not when
synthesis starts — regardless of how long the reply takes to speak.

Public API:
    speak(text: str, cooldown: bool = True) -> None
"""

import os
import tempfile
import threading
import time
import wave
from typing import Optional

import numpy as np
from playsound import playsound

from esp32 import display
from speech import mic_state
from speech.config import (
    PIPER_CONFIG_PATH,
    PIPER_MODEL_PATH,
    ROBOT_CARRIER_HZ,
    ROBOT_PITCH_SEMITONES,
    ROBOT_TREMOLO_DEPTH,
    ROBOT_TREMOLO_HZ,
    ROBOT_VOICE_ENABLED,
    ROBOT_WET_MIX,
)

try:
    from piper import PiperVoice
except ImportError:  # piper-tts not installed yet
    PiperVoice = None

_voice = None
_voice_load_error: Optional[str] = None

if PiperVoice is None:
    _voice_load_error = "piper-tts is not installed (pip install piper-tts)"
elif not os.path.isfile(PIPER_MODEL_PATH):
    _voice_load_error = (
        f"Piper voice model not found at {PIPER_MODEL_PATH}. Download one with:\n"
        f"  python -m piper.download_voices en_US-lessac-medium "
        f"--download-dir speech/voices"
    )
else:
    try:
        _voice = PiperVoice.load(PIPER_MODEL_PATH, config_path=PIPER_CONFIG_PATH)
    except Exception as exc:  # corrupt/incompatible model files, etc.
        _voice_load_error = f"Failed to load Piper voice: {exc}"


def _safe_remove(path: str, retries: int = 10, delay: float = 0.2) -> None:
    """Delete a temp file, retrying past Windows briefly holding the
    handle open right after playsound() returns. A leftover temp .wav
    if all retries fail is harmless, so this never raises.
    """
    for _ in range(retries):
        try:
            os.remove(path)
            return
        except FileNotFoundError:
            return
        except PermissionError:
            time.sleep(delay)


def _pitch_shift(samples: np.ndarray, semitones: float) -> np.ndarray:
    """Shift pitch by resampling (also changes duration/speed, which
    reads as intentionally mechanical rather than a bug here).
    """
    if semitones == 0:
        return samples

    factor = 2 ** (semitones / 12.0)
    new_length = max(1, int(len(samples) / factor))
    old_indices = np.linspace(0, len(samples) - 1, new_length)
    return np.interp(old_indices, np.arange(len(samples)), samples).astype(np.float32)


def _robotize(samples: np.ndarray, sample_rate: int) -> np.ndarray:
    """Turn a natural Piper voice into a cartoonish robotic voice.

    Ring modulation (multiplying by a low-frequency carrier tone) is the
    classic sci-fi robot voice effect; a slight pitch-down adds weight;
    a slow amplitude tremolo adds a chirpy, less-monotone "cartoon robot"
    flutter instead of a flat buzz; soft clipping adds digital grit.
    Blended with the dry signal via ROBOT_WET_MIX so words stay
    intelligible.
    """
    audio = samples.astype(np.float32)

    audio = _pitch_shift(audio, ROBOT_PITCH_SEMITONES)

    t = np.arange(len(audio)) / sample_rate

    carrier = np.sin(2 * np.pi * ROBOT_CARRIER_HZ * t)
    modulated = audio * carrier

    tremolo = 1.0 - ROBOT_TREMOLO_DEPTH + ROBOT_TREMOLO_DEPTH * np.sin(
        2 * np.pi * ROBOT_TREMOLO_HZ * t
    )
    modulated *= tremolo

    mixed = (1 - ROBOT_WET_MIX) * audio + ROBOT_WET_MIX * modulated
    mixed = np.tanh(mixed / 9000.0) * 9000.0  # mild soft clipping for grit

    peak = np.max(np.abs(mixed))
    if peak > 0:
        mixed *= (32767.0 * 0.9) / peak

    return np.clip(mixed, -32768, 32767).astype(np.int16)


def _synthesize_to_wav(text: str) -> str:
    """Render `text` to a temporary WAV file and return its path."""
    handle = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    path = handle.name
    handle.close()

    with wave.open(path, "wb") as wav_file:
        _voice.synthesize_wav(text, wav_file)

    if not ROBOT_VOICE_ENABLED:
        return path

    with wave.open(path, "rb") as wav_file:
        n_channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        sample_rate = wav_file.getframerate()
        raw = wav_file.readframes(wav_file.getnframes())

    if sample_width != 2 or n_channels != 1:
        # Ring-mod/pitch-shift math below assumes mono 16-bit samples;
        # skip processing rather than risk corrupting an unexpected format.
        return path

    samples = np.frombuffer(raw, dtype=np.int16)
    robotized = _robotize(samples, sample_rate)

    with wave.open(path, "wb") as wav_file:
        wav_file.setnchannels(n_channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(robotized.tobytes())

    return path


def speak(text: str, cooldown: bool = True) -> None:
    """Speak `text` aloud via Piper, with the mic locked for the full
    duration of playback.

    Non-blocking: synthesis and playback happen on a background thread,
    matching the fire-and-forget pattern speech/sound.py already uses,
    so the caller (app.py) never stalls waiting for speech to finish.

    `cooldown=True` (default) starts the post-speech cooldown once
    playback actually ends. Pass `cooldown=False` if this is ever used
    somewhere that should resume listening immediately instead.
    """
    text = (text or "").strip()
    if not text:
        return

    if _voice is None:
        print(f"[Piper not ready — {_voice_load_error}]\nWould say: {text}")
        return

    display.speaking()  # locks the mic (see esp32/display.py)

    def _run() -> None:
        path = _synthesize_to_wav(text)
        try:
            playsound(path)
        finally:
            _safe_remove(path)
        mic_state.unlock_microphone_and_start_cooldown(cooldown=cooldown)

    threading.Thread(target=_run, daemon=True).start()