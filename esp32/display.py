import requests

ESP32_IP = "192.168.137.217"   # Replace with your ESP32 IP


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


def ready():
    send("ready")


def listening():
    send("listening")


def thinking():
    send("thinking")


def speaking():
    send("speaking")


def sleep():
    send("sleep")