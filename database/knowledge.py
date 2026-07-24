from database.search import search_teacher, search_place
from utils.query import extract_keywords


def unique_rows(rows):
    """Remove duplicate SQLite rows based on ID."""
    seen = set()
    unique = []

    for row in rows:
        if row["id"] not in seen:
            seen.add(row["id"])
            unique.append(row)

    return unique


def build_teacher_context(teachers):
    context = []

    for teacher in teachers:
        info = [
            f"Teacher: {teacher['name']}",
            f"Designation: {teacher['designation']}",
            f"Department: {teacher['department']}",
        ]

        if teacher["room"]:
            info.append(f"Room: {teacher['room']}")

        if teacher["email"]:
            info.append(f"Email: {teacher['email']}")

        if teacher["office_hours"]:
            info.append(f"Office Hours: {teacher['office_hours']}")

        context.append("\n".join(info))

    return context


def build_place_context(places):
    context = []

    for place in places:
        info = [
            f"Place: {place['name']}"
        ]

        if place["building"]:
            info.append(f"Building: {place['building']}")

        if place["floor"]:
            info.append(f"Floor: {place['floor']}")

        if place["description"]:
            info.append(f"Description: {place['description']}")

        context.append("\n".join(info))

    return context


def retrieve_context(question):
    keywords = extract_keywords(question)

    if not keywords:
        keywords = [question]

    teachers = []
    places = []

    for keyword in keywords:
        teachers.extend(search_teacher(keyword))
        places.extend(search_place(keyword))

    teachers = unique_rows(teachers)
    places = unique_rows(places)

    context = []

    context.extend(build_teacher_context(teachers))
    context.extend(build_place_context(places))

    return "\n\n".join(context)