"""Streams a Piper-generated WAV file to the ESP32's speaker over UDP.

Reads 16-bit PCM audio, resamples it to 16000 Hz to match the ESP32
firmware's fixed DAC playback rate (see speaker.h), and streams it in
paced chunks followed by a 4-byte END marker so the firmware knows
when playback has finished and can resume the microphone.
"""

import socket
import time
import wave
from typing import Tuple

import numpy as np

from speech.config import ESP32_IP

# Must match speaker.h's SPEAKER_PORT exactly.
SPEAKER_PORT = 5006

# Must match speaker.h's SPEAKER_SAMPLE_RATE exactly.
SAMPLE_RATE = 16000

# Matches the ESP32 firmware's UDP read buffer (1024 bytes = 512 int16
# samples) so packets never get truncated on the receiving end.
CHUNK_SAMPLES = 512

# Must match speaker.h's SPEAKER_END_MARKER exactly (4 bytes, ASCII "END!").
END_MARKER = b"END!"

# Sent immediately, back-to-back, before real-time pacing kicks in, so
# the ESP32's ring buffer has a head start rather than starting empty.
# Without this, the very first network hiccup causes an underrun
# (audible click/static) right at the start of playback.
_PREBUFFER_CHUNKS = 6  # ~0.19s at 512 samples/chunk @ 16kHz

# Pace slightly FASTER than real-time (a small, bounded margin - not
# fully unpaced) so ordinary WiFi/OS jitter doesn't starve the buffer
# mid-word. Too aggressive a margin would eventually overflow the
# firmware's ~0.5s ring buffer on long replies; 0.95 keeps drift small.
_PACE_FACTOR = 0.95

_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def _resample(samples: np.ndarray, from_rate: int, to_rate: int) -> np.ndarray:
    """Linear-interpolation resample to the ESP32's fixed playback rate."""
    if from_rate == to_rate or len(samples) == 0:
        return samples.astype(np.int16)

    duration = len(samples) / from_rate
    new_length = max(1, int(round(duration * to_rate)))
    old_indices = np.linspace(0, len(samples) - 1, new_length)
    return np.interp(old_indices, np.arange(len(samples)), samples).astype(np.int16)


def _read_wav_mono16(path: str) -> Tuple[np.ndarray, int]:
    """Read a WAV file and return (samples, sample_rate) as mono int16.

    Stereo files are averaged down to mono. Raises ValueError instead
    of silently producing garbage audio if the file isn't 16-bit PCM.
    """
    with wave.open(path, "rb") as wav_file:
        n_channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        sample_rate = wav_file.getframerate()
        raw = wav_file.readframes(wav_file.getnframes())

    if sample_width != 2:
        raise ValueError(f"{path}: expected 16-bit PCM, got {sample_width * 8}-bit")

    samples = np.frombuffer(raw, dtype=np.int16)

    if n_channels == 2:
        samples = samples.reshape(-1, 2).mean(axis=1).astype(np.int16)
    elif n_channels != 1:
        raise ValueError(f"{path}: expected mono or stereo, got {n_channels} channels")

    return samples, sample_rate


def stream_to_esp32(path: str) -> None:
    """Read a Piper-generated WAV file and stream it to the ESP32 speaker.

    Blocking: the first few chunks are sent back-to-back to give the
    firmware's ring buffer a head start, then the rest are paced
    slightly faster than real-time so ordinary network/OS jitter can't
    starve the buffer mid-word (which sounds like crackling/static).
    Always sends the END marker on the way out, even for empty/silent
    audio, so the ESP32 never gets stuck waiting for a marker that
    never arrives.

    Call this from a background thread if the caller shouldn't stall
    for the full reply duration (see speech/voice.py).
    """
    samples, sample_rate = _read_wav_mono16(path)
    resampled = _resample(samples, sample_rate, SAMPLE_RATE)

    chunk_duration = CHUNK_SAMPLES / SAMPLE_RATE
    pace_delay = chunk_duration * _PACE_FACTOR

    chunk_starts = list(range(0, len(resampled), CHUNK_SAMPLES))

    for i, start in enumerate(chunk_starts):
        chunk = resampled[start:start + CHUNK_SAMPLES]
        try:
            _sock.sendto(chunk.tobytes(), (ESP32_IP, SPEAKER_PORT))
        except OSError:
            # Transient network hiccup: skip this chunk rather than
            # crash the speaking thread over one dropped packet.
            pass

        if i >= _PREBUFFER_CHUNKS:
            time.sleep(pace_delay)

    try:
        _sock.sendto(END_MARKER, (ESP32_IP, SPEAKER_PORT))
    except OSError:
        pass