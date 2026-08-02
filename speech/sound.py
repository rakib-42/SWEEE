import os
import random
import threading
from playsound import playsound

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _play(filename):
    path = os.path.join(BASE_DIR, filename)

    if os.path.exists(path):
        threading.Thread(
            target=playsound,
            args=(path,),
            daemon=True
        ).start()


def play_startup():
    _play("startup.mp3")


def play_shutdown():
    _play("shutdown.mp3")


def play_beep():
    _play("beep.mp3")


def play_intro():
    _play("intro.mp3")


def play_yes():
    _play("yes.mp3")


def play_happy():
    _play("happy.mp3")


def play_sad():
    _play("sad.mp3")


def play_cry():
    _play("cry.mp3")


def play_annoyed():
    _play("annoyed.mp3")


def play_tired():
    _play("tired.mp3")


def play_wallee():
    _play("wallee.mp3")


def play_random_whisper():
    whispers = [
        "whisper1.mp3",
        "whisper2.mp3",
    ]

    _play(random.choice(whispers))