import random
import threading
import time

from speech.sound import play_random_whisper


running = False


def idle_loop():
    global running

    running = True

    while running:
        wait = random.randint(16, 47)  # 2-5 minutes
        time.sleep(wait)

        if running:
            play_random_whisper()


def start_idle_sound():
    threading.Thread(
        target=idle_loop,
        daemon=True
    ).start()


def stop_idle_sound():
    global running
    running = False