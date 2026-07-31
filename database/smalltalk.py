import random


RESPONSES = {

    # Greetings
    "hi": [
        "Hello!",
        "Hi there!",
        "Hey!"
    ],

    "hello": [
        "Hello!",
        "Hi there!",
        "Hey!"
    ],

    "hey": [
        "Hey!",
        "Hello!",
        "Hi!"
    ],

    "good morning": [
        "Good morning!",
        "Good morning! How can I help you today?"
    ],

    "good afternoon": [
        "Good afternoon!",
        "Hope you're having a great day!"
    ],

    "good evening": [
        "Good evening!",
        "Good evening! How can I help?"
    ],

    "good night": [
        "Good night!",
        "Sleep well!"
    ],

    # Farewell
    "bye": [
        "Goodbye!",
        "See you later!",
        "Take care!"
    ],

    "goodbye": [
        "Goodbye!",
        "See you again!"
    ],

    "see you": [
        "See you soon!",
        "Take care!"
    ],

    "take care": [
        "You too!",
        "Take care!"
    ],

    # Thanks
    "thanks": [
        "You're welcome!",
        "Happy to help!"
    ],

    "thank you": [
        "You're welcome!",
        "My pleasure!"
    ],

    "thx": [
        "You're welcome!"
    ],

    "ty": [
        "You're welcome!"
    ],

        # About SWEEE
    "how are you": [
        "I'm doing great! How can I help you today?",
        "I'm functioning perfectly. How can I assist you?"
    ],

    "how are u": [
        "I'm doing great! How can I help you today?"
    ],

    "who are you": [
        "I'm SWEEE, your Software Engineering Educational Expert.",
        "I'm SWEEE, an AI assistant built to help with campus and academic information."
    ],

    "what are you": [
        "I'm SWEEE, your Software Engineering Educational Expert."
    ],

    "what is your name": [
        "My name is SWEEE."
    ],

    "what's your name": [
        "My name is SWEEE."
    ],

    "whats your name": [
        "My name is SWEEE."
    ],

    "who made you": [
        "I was developed as a Software Engineering prototype project."
    ],

    "who created you": [
        "I was developed as a Software Engineering prototype project."
    ],

    "what can you do": [
        "I can help you find teachers, rooms, campus locations, and answer academic questions."
    ],

    "help": [
        "You can ask me about teachers, rooms, offices, departments, or campus places."
    ],

    # Casual
    "ok": [
        "👍"
    ],

    "okay": [
        "👍"
    ],

    "alright": [
        "👍"
    ],

    "nice": [
        "😊"
    ],

    "cool": [
        "😎"
    ],

    "awesome": [
        "😄"
    ],

    "good job": [
        "Thank you!"
    ],

    # Greeting Variations
    
    "hello sweee": [
        "Hello! How can I help you today?"
    ],

    "hi sweee": [
        "Hi! What can I do for you?"
    ],

    "hey sweee": [
        "Hey! How can I assist you?"
    ],

    "good to see you": [
        "It's good to see you too!"
    ],

    "long time no see": [
        "Welcome back!"
    ],

    # Farewell Variations
    "see ya": [
        "See you soon!"
    ],

    "cya": [
        "Take care!"
    ],

    "catch you later": [
        "See you later!"
    ],

    # Thanks Variations
    "thank u": [
        "You're welcome!"
    ],

    "thanks a lot": [
        "You're very welcome!"
    ],

    "many thanks": [
        "Happy to help!"
    ],

    "thank you so much": [
        "You're very welcome!"
    ],

    # Positive Responses
    "great": [
        "😊"
    ],

    "excellent": [
        "😄"
    ],

    "perfect": [
        "Glad to hear that!"
    ],

    "amazing": [
        "😊"
    ],

    # Apology
    "sorry": [
        "No worries!"
    ],

    "my bad": [
        "It's okay!"
    ],

    # Confirmation
    "yes": [
        "Alright!"
    ],

    "yeah": [
        "👍"
    ],

    "yep": [
        "👍"
    ],

    "no": [
        "Alright."
    ],

    "nope": [
        "Okay."
    ]

}


def smalltalk(question):
    question = " ".join(question.lower().split())

    if question in RESPONSES:
        return random.choice(RESPONSES[question])

    return None