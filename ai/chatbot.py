from ollama import chat

from ai.memory import messages
from database.search import find_room
from utils.parser import extract_room_number
from ai.rag import answer_from_context


def ask(question):
    room = extract_room_number(question)

    if room:
        info = find_room(room)

        if info:
            context = f"""
Room Number: {info['room_number']}
Room Name: {info['room_name']}
Floor: {info['floor']}
"""

            return answer_from_context(question, context)

    messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    response = chat(
        model="qwen2.5:1.5b",
        messages=messages
    )

    answer = response["message"]["content"]

    messages.append(
        {
            "role": "assistant",
            "content": answer
        }
    )

    return answer