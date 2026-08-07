"""Central configuration for the SWEEE speech pipeline.

Every tunable used by listener.py, mic_state.py, voice.py, and the
display-layer mic-lock hooks in esp32/display.py lives here so nothing
is hardcoded inline elsewhere in the speech package.
"""

import os
from typing import List

# ---------------------------------------------------------------------------
# ESP32 / audio transport
# ---------------------------------------------------------------------------

ESP32_IP: str = "192.168.137.3"
UDP_PORT: int = 5005

SAMPLE_RATE: int = 16000
FRAME_SAMPLES: int = 512  # required chunk size for Silero VAD at 16 kHz

# ---------------------------------------------------------------------------
# Recording state machine
# ---------------------------------------------------------------------------

PRE_ROLL_SECONDS: float = 0.5
MIN_SPEECH_SECONDS: float = 0.7

# Adaptive silence timeout: short commands end quickly, longer sentences
# get more room to pause without being cut off mid-thought.
SHORT_SILENCE_TIMEOUT_MS: int = 600
LONG_SILENCE_TIMEOUT_MS: int = 1100
LONG_UTTERANCE_THRESHOLD_SECONDS: float = 2.5

SPEECH_PROB_THRESHOLD: float = 0.5

# ---------------------------------------------------------------------------
# Audio normalization
# ---------------------------------------------------------------------------

TARGET_RMS_RATIO: float = 0.15
TARGET_PEAK_RATIO: float = 0.9
MAX_GAIN: float = 4.0
NOISE_GATE_THRESHOLD: float = 300.0
NOISE_GATE_ATTENUATION: float = 0.25

# ---------------------------------------------------------------------------
# Vocabulary / correction pipeline
# ---------------------------------------------------------------------------

FUZZY_MATCH_THRESHOLD: float = 90.0
VOCABULARY_PATH: str = "database/vocabulary.txt"
CORRECTIONS_PATH: str = "database/corrections.json"
FALLBACK_PROMPT: str = ""

# ---------------------------------------------------------------------------
# Wake word / conversation flow
# ---------------------------------------------------------------------------

WAKE_WORDS: List[str] = [
    "wall-e",
    "wall e",
    "wally",
]

CONFIRMATION_TEXT: str = "Yes?"

COOLDOWN_SECONDS: float = 10.0

# ---------------------------------------------------------------------------
# Piper TTS (speech/voice.py)
# ---------------------------------------------------------------------------

# "lessac" is a female voice, which is likely why it read as "girly."
# "danny" is male; the "-low" quality tier also happens to sound more
# synthetic/cartoonish out of the box than "-medium" (smaller model,
# less natural prosody) — a reasonable starting point before the robot
# effect below is even applied, and it's lighter on your CPU too.
# Download with:
#   python -m piper.download_voices en_US-danny-low --download-dir speech/voices
PIPER_VOICE_DIR: str = "speech/voices"
PIPER_VOICE_NAME: str = "en_US-lessac-medium"

PIPER_MODEL_PATH: str = os.path.join(PIPER_VOICE_DIR, f"{PIPER_VOICE_NAME}.onnx")
PIPER_CONFIG_PATH: str = os.path.join(PIPER_VOICE_DIR, f"{PIPER_VOICE_NAME}.onnx.json")

# Wall-E / AUTO-style robotic voice effect, applied to Piper's output
# before playback (ring modulation + slight pitch-down + soft digital
# grit). Piper itself only produces natural human voices, so this is a
# post-processing pass on top of it, not a different voice model.
ROBOT_VOICE_ENABLED: bool = True
ROBOT_CARRIER_HZ: float = 120.0       # ring-mod carrier tone; higher = buzzier/more metallic
ROBOT_WET_MIX: float = 0.45           # 0.0 = unprocessed Piper voice, 1.0 = fully ring-modulated
ROBOT_PITCH_SEMITONES: float = -1.0  # negative = deeper/slower, 0 = no pitch shift
ROBOT_TREMOLO_HZ: float = 13.0        # amplitude wobble rate; gives a "chirpy/cartoonish" flutter
ROBOT_TREMOLO_DEPTH: float = 0.30    # 0.0 = no wobble, 1.0 = pulses fully on/off