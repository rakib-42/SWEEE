"""ESP32 (INMP441) microphone listener with wake word + command flow.

Receives PCM16 audio over UDP from an ESP32, detects utterances with
Silero VAD using an Alexa-style "wait for speech -> record -> silence
timeout" state machine, and transcribes each utterance with
faster-whisper. Recognition of proper nouns is improved with a dynamic
vocabulary prompt, a JSON correction table, and rapidfuzz-based fuzzy
correction.

Conversation flow:
    Wake Mode -> wake word detected -> "Yes?" (yes.mp3, mic locked)
    -> Command Mode -> one command recorded and transcribed -> text
       returned to the caller, which passes it to the existing
       ai.chatbot.ask() unchanged.

The mic-lock + cooldown around the AI's *spoken reply* is handled in
esp32/display.py (see speaking()/ready()), not here — ai/chatbot.py
already calls those on every reply branch, so hooking them there means
this feature needs zero changes to ai/chatbot.py.

Public API:
    text = listen()
"""

import json
import os
import re
import socket
import tempfile
import threading
import wave
from collections import deque
from typing import Deque, Dict, List, Optional

import numpy as np
import torch
from faster_whisper import WhisperModel
from playsound import playsound
from rapidfuzz import fuzz, process
from silero_vad import load_silero_vad

from esp32 import display
from speech import mic_state
from speech.config import (
    CONFIRMATION_TEXT,
    CORRECTIONS_PATH,
    ESP32_IP,
    FALLBACK_PROMPT,
    FRAME_SAMPLES,
    FUZZY_MATCH_THRESHOLD,
    LONG_SILENCE_TIMEOUT_MS,
    LONG_UTTERANCE_THRESHOLD_SECONDS,
    MAX_GAIN,
    MIN_SPEECH_SECONDS,
    NOISE_GATE_ATTENUATION,
    NOISE_GATE_THRESHOLD,
    PRE_ROLL_SECONDS,
    SAMPLE_RATE,
    SHORT_SILENCE_TIMEOUT_MS,
    SPEECH_PROB_THRESHOLD,
    TARGET_PEAK_RATIO,
    TARGET_RMS_RATIO,
    UDP_PORT,
    VOCABULARY_PATH,
    WAKE_WORDS,
)

PRE_ROLL_FRAMES: int = max(1, int(PRE_ROLL_SECONDS * SAMPLE_RATE / FRAME_SAMPLES))
MIN_SPEECH_SAMPLES: int = int(MIN_SPEECH_SECONDS * SAMPLE_RATE)

# yes.mp3 already exists in speech/ (see speech/sound.py) and is reused
# here directly, rather than modifying sound.py, since the confirmation
# needs a completion callback (to unlock the mic) that sound.py's
# fire-and-forget _play() doesn't expose.
_YES_MP3_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yes.mp3")


class _FrameSource:
    """Re-frames arbitrary-sized UDP packets into fixed-size PCM16 chunks.

    Keeps only a small leftover buffer (smaller than one frame) between
    calls, so memory stays bounded no matter how long the listener runs.
    """

    def __init__(self, sock: socket.socket, frame_samples: int) -> None:
        self._sock = sock
        self._frame_samples = frame_samples
        self._leftover = np.array([], dtype=np.int16)

    def next_frame(self) -> np.ndarray:
        """Block until a full frame of audio is available and return it."""
        while len(self._leftover) < self._frame_samples:
            data, _ = self._sock.recvfrom(4096)
            if not data:
                continue
            packet = np.frombuffer(data, dtype=np.int16)
            self._leftover = np.concatenate((self._leftover, packet))

        frame = self._leftover[: self._frame_samples]
        self._leftover = self._leftover[self._frame_samples:]
        return frame


def _next_gated_frame(frames: _FrameSource) -> np.ndarray:
    """Return the next frame, silently draining (never processing) audio
    while the microphone is locked or in its cooldown window.

    This is the single choke point that keeps Silero/Whisper from ever
    seeing the robot's own voice or post-speech noise, without blocking
    the UDP socket (Requirements 2, 3, 7).
    """
    while True:
        frame = frames.next_frame()
        if mic_state.is_audio_accepted():
            return frame


def _create_socket() -> socket.socket:
    """Open the UDP socket and handshake with the ESP32."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", UDP_PORT))
    sock.sendto(b"HELLO", (ESP32_IP, UDP_PORT))
    return sock


def _is_speech(frame: np.ndarray, vad_model) -> bool:
    """Return True if the given frame is classified as speech by Silero VAD."""
    audio_tensor = torch.from_numpy(frame.astype(np.float32) / 32768.0)
    with torch.no_grad():
        probability = vad_model(audio_tensor, SAMPLE_RATE).item()
    return probability >= SPEECH_PROB_THRESHOLD


def _current_silence_timeout_frames(recorded_duration_seconds: float) -> int:
    """Pick a silence timeout based on how long the utterance has run so far."""
    timeout_ms = (
        LONG_SILENCE_TIMEOUT_MS
        if recorded_duration_seconds >= LONG_UTTERANCE_THRESHOLD_SECONDS
        else SHORT_SILENCE_TIMEOUT_MS
    )
    return max(1, int(timeout_ms / 1000 * SAMPLE_RATE / FRAME_SAMPLES))


# ---------------------------------------------------------------------------
# Audio normalization
# ---------------------------------------------------------------------------

def _normalize_audio(samples: np.ndarray) -> np.ndarray:
    """Clean up a recorded utterance before it reaches Whisper.

    Steps: remove DC offset, apply a light noise gate to quiet segments,
    then normalize loudness using whichever of RMS/peak gain is smaller
    (so we never clip and never blast up a mostly-silent recording).
    """
    audio = samples.astype(np.float32)

    audio -= np.mean(audio)

    quiet_mask = np.abs(audio) < NOISE_GATE_THRESHOLD
    audio[quiet_mask] *= NOISE_GATE_ATTENUATION

    rms = float(np.sqrt(np.mean(np.square(audio)))) if audio.size else 0.0
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0

    if rms <= 0.0 or peak <= 0.0:
        return np.clip(audio, -32768, 32767).astype(np.int16)

    rms_gain = (32768.0 * TARGET_RMS_RATIO) / rms
    peak_gain = (32767.0 * TARGET_PEAK_RATIO) / peak
    gain = min(rms_gain, peak_gain, MAX_GAIN)

    audio *= gain
    audio = np.clip(audio, -32768, 32767)
    return audio.astype(np.int16)


def _write_wav(samples: np.ndarray) -> str:
    """Write samples to a temporary mono 16 kHz PCM16 WAV file, return its path."""
    handle = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    path = handle.name
    handle.close()

    with wave.open(path, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(samples.tobytes())

    return path


# ---------------------------------------------------------------------------
# Vocabulary prompt + correction dictionary (loaded once)
# ---------------------------------------------------------------------------

def _load_vocabulary(path: str) -> List[str]:
    """Load one vocabulary entry per line. Returns [] if the file is missing."""
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as vocab_file:
        return [line.strip() for line in vocab_file if line.strip()]


def _merge_wake_words(vocabulary: List[str], wake_words: List[str]) -> List[str]:
    """Fold the wake words into the vocabulary list (case-insensitive dedupe)
    so they benefit from the same Whisper prompt priming and fuzzy
    correction as any other proper noun.
    """
    merged = list(vocabulary)
    seen = {word.lower() for word in merged}
    for word in wake_words:
        if word.lower() not in seen:
            merged.append(word)
            seen.add(word.lower())
    return merged


def _build_initial_prompt(vocabulary: List[str]) -> str:
    """Turn the vocabulary list into a Whisper initial_prompt / hotwords string."""
    if not vocabulary:
        return FALLBACK_PROMPT
    words = ", ".join(vocabulary)
    return f"This conversation may include the following names and words: {words}."


def _load_corrections(path: str) -> Dict[str, str]:
    """Load the phrase-correction table. Returns {} if the file is missing."""
    if not os.path.isfile(path):
        return {}
    with open(path, "r", encoding="utf-8") as corrections_file:
        return json.load(corrections_file)


# ---------------------------------------------------------------------------
# Post-processing: exact corrections + fuzzy matching
# ---------------------------------------------------------------------------

def _apply_corrections(text: str, corrections: Dict[str, str]) -> str:
    """Replace known mis-transcribed phrases using an exact, case-insensitive match."""
    if not corrections:
        return text

    # Longest keys first so multi-word phrases are matched before their
    # shorter substrings (e.g. "super of" before "super").
    for wrong in sorted(corrections, key=len, reverse=True):
        correct = corrections[wrong]
        pattern = re.compile(rf"\b{re.escape(wrong)}\b", re.IGNORECASE)
        text = pattern.sub(correct, text)

    return text


def _fuzzy_lookup(candidate: str, vocabulary: List[str]) -> Optional[str]:
    """Return the closest vocabulary entry if it's a >=90% match, else None."""
    match = process.extractOne(
        candidate,
        vocabulary,
        scorer=fuzz.ratio,
        score_cutoff=FUZZY_MATCH_THRESHOLD,
    )
    return match[0] if match else None


def _apply_fuzzy_corrections(text: str, vocabulary: List[str]) -> str:
    """Fuzzy-correct remaining words/phrases against the vocabulary list.

    Tries a two-word window first (covers phrases like "Room 602" or
    "Wall E"), then falls back to a single word. Only replaces on a
    >=90% similarity match.
    """
    if not vocabulary:
        return text

    words = text.split()
    result: List[str] = []
    i = 0

    while i < len(words):
        if i + 1 < len(words):
            bigram = f"{words[i]} {words[i + 1]}"
            match = _fuzzy_lookup(bigram, vocabulary)
            if match:
                result.append(match)
                i += 2
                continue

        match = _fuzzy_lookup(words[i], vocabulary)
        result.append(match if match else words[i])
        i += 1

    return " ".join(result)


def _postprocess_text(text: str, corrections: Dict[str, str], vocabulary: List[str]) -> str:
    """Run the full correction pipeline on raw Whisper output."""
    text = _apply_corrections(text, corrections)
    text = _apply_fuzzy_corrections(text, vocabulary)
    return text


def _contains_wake_word(text: str, wake_words: List[str]) -> bool:
    """True if the (already corrected) text contains any configured wake word."""
    normalized = text.lower().replace("-", " ")
    for word in wake_words:
        if word.lower().replace("-", " ") in normalized:
            return True
    return False


# ---------------------------------------------------------------------------
# Transcription
# ---------------------------------------------------------------------------

def _transcribe(path: str, whisper: WhisperModel, initial_prompt: str) -> str:
    """Transcribe a WAV file with Whisper and return the raw stripped text."""
    common_kwargs = dict(
        language="en",
        beam_size=5,
        condition_on_previous_text=False,
        vad_filter=False,
        temperature=0.0,
        initial_prompt=initial_prompt or None,
    )
    try:
        # "hotwords" (newer faster-whisper releases) biases decoding toward
        # specific words with negligible extra latency, on top of the
        # initial_prompt. Fall back gracefully on older versions.
        segments, _ = whisper.transcribe(
            path, hotwords=initial_prompt or None, **common_kwargs
        )
    except TypeError:
        segments, _ = whisper.transcribe(path, **common_kwargs)

    return "".join(segment.text for segment in segments).strip()


def _record_utterance(frames: _FrameSource, vad_model) -> np.ndarray:
    """Run the wait-for-speech / record / adaptive-silence-timeout state
    machine for a single utterance and return the captured samples,
    including the pre-roll leading up to the detected speech onset.

    Every frame is fetched through `_next_gated_frame`, so this loop is
    automatically a no-op (just draining audio) while the mic is locked
    or cooling down. It's reused for both wake-word spotting and full
    command recording.
    """
    vad_model.reset_states()

    pre_roll: Deque[np.ndarray] = deque(maxlen=PRE_ROLL_FRAMES)

    frame = _next_gated_frame(frames)
    while not _is_speech(frame, vad_model):
        pre_roll.append(frame)
        frame = _next_gated_frame(frames)

    recorded_frames: List[np.ndarray] = list(pre_roll) + [frame]
    total_samples = sum(len(f) for f in recorded_frames)
    silence_run = 0

    while True:
        frame = _next_gated_frame(frames)
        recorded_frames.append(frame)
        total_samples += len(frame)

        if _is_speech(frame, vad_model):
            silence_run = 0
            continue

        silence_run += 1
        duration_so_far = total_samples / SAMPLE_RATE
        if silence_run >= _current_silence_timeout_frames(duration_so_far):
            break

    return np.concatenate(recorded_frames)


def _transcribe_utterance(
    samples: np.ndarray,
    whisper: WhisperModel,
    initial_prompt: str,
    corrections: Dict[str, str],
    vocabulary: List[str],
) -> str:
    """Normalize, write, transcribe, correct, and clean up one utterance."""
    normalized = _normalize_audio(samples)

    print("📝 Transcribing...")

    path = _write_wav(normalized)
    try:
        raw_text = _transcribe(path, whisper, initial_prompt)
    finally:
        os.remove(path)

    return _postprocess_text(raw_text, corrections, vocabulary)


# ---------------------------------------------------------------------------
# Module-level state (loaded once, reused for the lifetime of the process)
# ---------------------------------------------------------------------------

_whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
_vad_model = load_silero_vad()
_socket = _create_socket()
_frame_source = _FrameSource(_socket, FRAME_SAMPLES)

_vocabulary = _merge_wake_words(_load_vocabulary(VOCABULARY_PATH), WAKE_WORDS)
_initial_prompt = _build_initial_prompt(_vocabulary)
_corrections = _load_corrections(CORRECTIONS_PATH)

display.idle()


# ---------------------------------------------------------------------------
# Wake Mode / Command Mode
# ---------------------------------------------------------------------------

def _wait_for_wake_word() -> None:
    """Stay in Wake Mode, capturing and transcribing short utterances,
    until one of them contains a configured wake word. Never calls the AI.
    """
    print("🎤 Wake Mode")
    display.listening()

    while True:
        samples = _record_utterance(_frame_source, _vad_model)

        if len(samples) < MIN_SPEECH_SAMPLES:
            continue

        text = _transcribe_utterance(
            samples, _whisper_model, _initial_prompt, _corrections, _vocabulary
        )

        if _contains_wake_word(text, WAKE_WORDS):
            return


def _confirm_wake() -> None:
    """Acknowledge the wake word immediately with the hardcoded "Yes?"
    audio clip (speech/yes.mp3) — no AI call. Locks the mic for the
    duration of playback and unlocks with NO cooldown afterward, so
    Command Mode starts listening right away.
    """
    print("👂 Wake word detected")
    display.wake_detected()

    print("🗣", CONFIRMATION_TEXT)
    display.speaking()  # locks the mic (see esp32/display.py)

    def _play_confirmation() -> None:
        if os.path.exists(_YES_MP3_PATH):
            playsound(_YES_MP3_PATH)
        # No cooldown: Command Mode should start listening immediately.
        mic_state.unlock_microphone_and_start_cooldown(cooldown=False)

    threading.Thread(target=_play_confirmation, daemon=True).start()


def _record_command() -> str:
    """Record and transcribe exactly one command in Command Mode."""
    print("🎤 Listening...")
    display.listening()

    while True:
        samples = _record_utterance(_frame_source, _vad_model)

        if len(samples) < MIN_SPEECH_SAMPLES:
            continue

        text = _transcribe_utterance(
            samples, _whisper_model, _initial_prompt, _corrections, _vocabulary
        )

        if text:
            return text


def listen() -> str:
    """Block until a full voice command has been captured, then return it.

    Runs the whole SWEEE conversation cycle internally: Wake Mode ->
    wake word detected -> hardcoded "Yes?" confirmation (mic locked
    while playing) -> Command Mode -> transcribed command text.

    Callers use this exactly as before:
        text = listen()
        reply = ask(text)

    Never returns None, never returns partial or empty speech, and
    never returns the wake word itself — only a real command.
    """
    _wait_for_wake_word()
    _confirm_wake()

    text = _record_command()

    print(f"👤 You: {text}")
    print("🤖 Thinking...")
    display.thinking()

    return text