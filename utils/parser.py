import re


def extract_room_number(text):
    match = re.search(r"\b\d{3}\b", text)

    if match:
        return match.group()

    return None