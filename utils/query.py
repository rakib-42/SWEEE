import re

STOP_WORDS = {
    "where", "what", "who", "when", "is", "are", "the", "a", "an",
    "of", "to", "in", "on", "at", "for", "tell", "me", "about",
    "please", "can", "you"
}


def extract_keywords(question):
    words = re.findall(r"[A-Za-z0-9]+", question.lower())

    keywords = [
        word
        for word in words
        if word not in STOP_WORDS and len(word) > 1
    ]

    return keywords