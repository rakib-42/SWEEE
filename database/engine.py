from database.search import search_teacher, search_place
from utils.query import extract_keywords


def teacher_answer(teacher, question):
    question = question.lower()

    # Room / Office
    if any(word in question for word in ["room", "office", "where"]):
        if teacher["room"]:
            return f"{teacher['name']}'s office is Room {teacher['room']}."
        return f"I couldn't find {teacher['name']}'s office."

    # Email
    if any(word in question for word in ["email", "mail"]):
        if teacher["email"]:
            return f"{teacher['name']}'s email is {teacher['email']}."
        return f"I couldn't find {teacher['name']}'s email."

    # Office Hours
    if any(word in question for word in ["office hour", "office hours", "available", "time"]):
        if teacher["office_hours"]:
            return f"{teacher['name']}'s office hours are {teacher['office_hours']}."
        return f"I couldn't find {teacher['name']}'s office hours."

    # Department
    if any(word in question for word in ["department", "dept"]):
        return f"{teacher['name']} is in the {teacher['department']} department."

    # Designation
    if any(word in question for word in ["designation", "position", "job"]):
        return f"{teacher['name']} is a {teacher['designation']}."

    # Default
    answer = [
        f"{teacher['name']} is a {teacher['designation']} in the {teacher['department']} department."
    ]

    if teacher["room"]:
        answer.append(f"Office: Room {teacher['room']}.")

    if teacher["email"]:
        answer.append(f"Email: {teacher['email']}.")

    if teacher["office_hours"]:
        answer.append(f"Office hours: {teacher['office_hours']}.")

    return " ".join(answer)


def place_answer(place, question):
    question = question.lower()

    if any(word in question for word in ["where", "location"]):
        answer = [place["name"]]

        if place["building"]:
            answer.append(f"is located in {place['building']} building.")

        if place["floor"]:
            answer.append(f"Floor {place['floor']}.")

        return " ".join(answer)

    answer = [place["name"]]

    if place["building"]:
        answer.append(f"is located in {place['building']} building.")

    if place["floor"]:
        answer.append(f"Floor {place['floor']}.")

    if place["description"]:
        answer.append(place["description"])

    return " ".join(answer)


def search(question):
    keywords = extract_keywords(question)

    if not keywords:
        keywords = [question]

    teachers = []
    places = []

    # Search only once
    for keyword in keywords:
        teachers.extend(search_teacher(keyword))
        places.extend(search_place(keyword))

    # Remove duplicates
    teachers = list({t["id"]: t for t in teachers}.values())
    places = list({p["id"]: p for p in places}.values())

    # Teacher
    if teachers:
        return {
            "found": True,
            "answer": teacher_answer(teachers[0], question),
            "source": "teacher",
            "teachers": teachers,
            "places": []
        }

    # Place
    if places:
        return {
            "found": True,
            "answer": place_answer(places[0], question),
            "source": "place",
            "teachers": [],
            "places": places
        }

    return {
        "found": False,
        "answer": None,
        "source": None,
        "teachers": [],
        "places": []
    }