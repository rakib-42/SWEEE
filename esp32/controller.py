import requests

ESP32_IP = "192.168.137.3"


def send(state):

    url = f"http://{ESP32_IP}/display"

    requests.get(
        url,
        params={
            "state": state
        },
        timeout=3
    )


if __name__ == "__main__":

    while True:

        print()

        state = input(
            "State : "
        ).strip().lower()

        send(state)