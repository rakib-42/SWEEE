import random

from database.search import search_teacher, search_place
from utils.query import extract_keywords


FOLLOWUP_INTENTS = {

    "room",
    "office",
    "where",
    "location",
    "located",
    "building",
    "floor",

    "email",
    "mail",
    "contact",
    "phone",
    "mobile",
    "telephone",
    "number",

    "department",
    "dept",
    "faculty",

    "designation",
    "position",
    "job",
    "role",
    "title",

    "office hour",
    "office hours",
    "available",
    "availability",
    "time",
    "timing",
    "schedule",

    "details",
    "detail",
    "info",
    "information",
    "profile",

    "he",
    "she",
    "his",
    "her",
    "him",
    "their",
    "them",
    "there",
}

DATABASE_INTENTS = {
    "room",
    "office",
    "where",
    "location",
    "located",
    "email",
    "mail",
    "contact",
    "phone",
    "mobile",
    "department",
    "faculty",
    "designation",
    "position",
    "role",
    "title",
    "office",
    "hours",
    "schedule",
    "available",
    "building",
    "floor",
    "teacher",
    "sir",
    "madam",
    "professor",
    "lecturer",
    "faculty"
}


CLARIFICATION_RESPONSES = [
    "Could you tell me who you're referring to?",
    "Which teacher or place do you mean?",
    "I need a little more context to answer that.",
    "Please tell me the teacher or place name.",
    "Whose information are you looking for?",
    "Can you specify the teacher or place first?",
    "I'm not sure who you're asking about.",
]

def should_search_database(question):
    question = question.lower()

    # Don't search DB for AI writing requests
    blocked = [
        "write",
        "paragraph",
        "essay",
        "story",
        "poem",
        "code",
        "program",
        "generate",
        "explain",
        "describe",
        "summarize",
        "summary",
        "what is",
        "how to"
    ]

    if any(word in question for word in blocked):
        return False

    return any(word in question for word in DATABASE_INTENTS)

def clarification():
    return random.choice(CLARIFICATION_RESPONSES)


def is_followup_question(question):
    question = " ".join(question.lower().split())
    return question in FOLLOWUP_INTENTS


def teacher_answer(teacher, question):
    teacher = dict(teacher)
    question = " ".join(question.lower().split())
    words = set(question.split())

    if question in {"id", "teacher id", "faculty id"}:
            return "Teacher IDs are not available in my database."

    # Office / Room
    if (
        "room" in words
        or "office" in words
        or question == "where"
        or question == "location"
    ):
        if teacher.get("room"):
            return f"{teacher['name']}'s office is Room {teacher['room']}."
        return f"I couldn't find {teacher['name']}'s office."

    # Email
    if "email" in words or "mail" in words:
        if teacher.get("email"):
            return f"{teacher['name']}'s email is {teacher['email']}."
        return f"I couldn't find {teacher['name']}'s email."

    # Office Hours
    if (
        question in {"office hour", "office hours"}
        or "available" in words
        or "availability" in words
        or "schedule" in words
        or "timing" in words
        or "time" in words
    ):
        if teacher.get("office_hours"):
            return f"{teacher['name']}'s office hours are {teacher['office_hours']}."
        return f"I couldn't find {teacher['name']}'s office hours."

    # Department
    if (
        "department" in words
        or "dept" in words
        or question == "faculty"
    ):
        return f"{teacher['name']} belongs to the {teacher['department']} department."

    # Designation
    if (
        "designation" in words
        or "position" in words
        or "job" in words
        or "role" in words
        or "title" in words
    ):
        return f"{teacher['name']} is a {teacher['designation']}."

    answer = [
        f"{teacher['name']} is a {teacher['designation']} in the {teacher['department']} department."
    ]

    if teacher.get("room"):
        answer.append(f"Office: Room {teacher['room']}.")

    if teacher.get("email"):
        answer.append(f"Email: {teacher['email']}.")

    if teacher.get("office_hours"):
        answer.append(f"Office hours: {teacher['office_hours']}.")

    return " ".join(answer)


def place_answer(place, question):
    place = dict(place)
    question = " ".join(question.lower().split())
    words = set(question.split())

    if (
        question == "where"
        or question == "location"
        or "building" in words
        or "floor" in words
    ):
        answer = [place["name"]]

        if place.get("building"):
            answer.append(f"is located in {place['building']} building.")

        if place.get("floor"):
            answer.append(f"Floor {place['floor']}.")

        return " ".join(answer)

    answer = [place["name"]]

    if place.get("building"):
        answer.append(f"is located in {place['building']} building.")

    if place.get("floor"):
        answer.append(f"Floor {place['floor']}.")

    if place.get("description"):
        answer.append(place["description"])

    return " ".join(answer)
def search(question, entity_memory=None):
    question = " ".join(question.strip().split())

    if not should_search_database(question):
        return {
            "found": False,
            "answer": None,
            "source": None,
            "teachers": [],
            "places": []
        }

    keywords = extract_keywords(question)

    if not keywords:
        keywords = [question]

    teachers = []
    places = []

    for keyword in keywords:
        teachers.extend(search_teacher(keyword))
        places.extend(search_place(keyword))

    # Remove duplicates
    teachers = list({t["id"]: t for t in teachers}.values())
    places = list({p["id"]: p for p in places}.values())

    # ---------------- Teacher ----------------
    if teachers:
        teacher = teachers[0]

        if entity_memory:
            entity_memory.remember_teacher(dict(teacher))

        return {
            "found": True,
            "answer": teacher_answer(teacher, question),
            "source": "teacher",
            "teachers": teachers,
            "places": []
        }

    # ---------------- Place ----------------
    if places:
        place = places[0]

        if entity_memory:
            entity_memory.remember_place(dict(place))

        return {
            "found": True,
            "answer": place_answer(place, question),
            "source": "place",
            "teachers": [],
            "places": places
        }

    # ---------------- Follow-up ----------------
    if is_followup_question(question):

        if entity_memory:

            teacher = entity_memory.get_teacher()

            if teacher:
                return {
                    "found": True,
                    "answer": teacher_answer(teacher, question),
                    "source": "memory",
                    "teachers": [teacher],
                    "places": []
                }

            place = entity_memory.get_place()

            if place:
                return {
                    "found": True,
                    "answer": place_answer(place, question),
                    "source": "memory",
                    "teachers": [],
                    "places": [place]
                }

        return {
            "found": True,
            "answer": clarification(),
            "source": "clarification",
            "teachers": [],
            "places": []
        }

    # ---------------- Nothing Found ----------------
    return {
        "found": False,
        "answer": None,
        "source": None,
        "teachers": [],
        "places": []
    }