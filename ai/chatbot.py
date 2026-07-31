from ollama import chat
from ai.personality import SYSTEM_PROMPT
from ai.rag import answer
from core.config import OLLAMA_MODEL
from memory.conversation import ConversationMemory
from database.engine import search

memory = ConversationMemory()


def ask(question):

    # ---------- Knowledge Engine ----------
    knowledge = search(question)

    if knowledge["found"]:
        memory.add_user(question)
        memory.add_assistant(knowledge["answer"])
        return knowledge["answer"]

    # ---------- RAG ----------
    reply = answer(question, "")

    if reply:
        memory.add_user(question)
        memory.add_assistant(reply)
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

    memory.add_assistant(answer_text)

    return answer_text