from ollama import chat

from ai.personality import SYSTEM_PROMPT
from ai.rag import answer
from core.config import OLLAMA_MODEL

from memory.conversation import ConversationMemory
from memory.entity import EntityMemory

from database.engine import search
from database.smalltalk import smalltalk

from esp32 import display

from speech.sound import (
    play_happy,
    play_sad,
    play_yes,
    play_annoyed,
)

memory = ConversationMemory()
entity_memory = EntityMemory()


def ask(question):

    display.thinking()

    # ---------- Small Talk ----------
    reply = smalltalk(question)

    if reply:
        play_happy()
        display.speaking()

        memory.add_user(question)
        memory.add_assistant(reply)

        entity_memory.clear()

        display.ready()

        return reply

    # ---------- Knowledge Engine ----------
    knowledge = search(question, entity_memory)

    if knowledge["found"]:
        play_happy()
        display.speaking()

        memory.add_user(question)
        memory.add_assistant(knowledge["answer"])

        entity_memory.clear()

        display.ready()

        return knowledge["answer"]

    # ---------- RAG ----------
    reply = answer(question, "")

    if reply:
        play_happy()
        display.speaking()

        memory.add_user(question)
        memory.add_assistant(reply)

        entity_memory.clear()

        display.ready()

        return reply

    # ---------- General AI ----------
    memory.add_user(question)

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    messages.extend(memory.get_history())

    response = chat(
        model=OLLAMA_MODEL,
        messages=messages
    )

    answer_text = response["message"]["content"].strip()

    if not answer_text:
        play_sad()

        entity_memory.clear()

        display.ready()

        return "Sorry, I couldn't find an answer."

    play_happy()
    display.speaking()

    memory.add_assistant(answer_text)

    entity_memory.clear()

    display.ready()

    return answer_text