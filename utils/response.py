import random

CLARIFICATION_RESPONSES = [
    "Could you tell me whose ID you're looking for?",
    "Which ID are you referring to?",
    "I need a little more context. Whose ID do you need?",
    "Can you specify the teacher or place you're asking about?",
    "I'm not sure which ID you mean. Could you be more specific?",
    "Whose ID would you like to know?",
]


def clarification():
    return random.choice(CLARIFICATION_RESPONSES)