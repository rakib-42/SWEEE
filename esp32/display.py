import threading
import time

import requests

from speech import mic_state
from speech.config import COOLDOWN_SECONDS

ESP32_IP = "192.168.137.3"   # Replace with your ESP32 IP


def send(state):

    try:

        requests.get(
            f"http://{ESP32_IP}/display",
            params={"state": state},
            timeout=1
        )

    except:
        pass


def boot():
    send("boot")


def idle():
    send("idle")


def ready():
    # ai/chatbot.py calls this exactly once, at the end of every reply
    # branch, right after the reaction sound (play_happy/play_sad/...)
    # has started playing. That makes it the one existing, unmodified
    # hook point for "the robot just finished speaking" -> start the
    # microphone cooldown here instead of touching chatbot.py itself.
    mic_state.unlock_microphone_and_start_cooldown(cooldown=True)
    send("cooldown")

    def _end_cooldown():
        time.sleep(COOLDOWN_SECONDS)
        send("idle")

    threading.Thread(target=_end_cooldown, daemon=True).start()


def listening():
    send("listening")


def thinking():
    send("thinking")


def speaking():
    # Locks the mic for as long as the robot is producing audio, so
    # Whisper/Silero never hear the robot's own voice (self-trigger
    # prevention). Every existing call to speaking() in chatbot.py is
    # immediately followed by a reaction sound, so this covers it with
    # no changes needed there.
    mic_state.lock_microphone()
    send("speaking")


def wake_detected():
    send("wake_detected")


def cooldown():
    send("cooldown")


def sleep():
    send("sleep")