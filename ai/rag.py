from ollama import chat

from ai.personality import SYSTEM_PROMPT
from core.config import OLLAMA_MODEL
from database.knowledge import retrieve_context


RAG_PROMPT = (
    SYSTEM_PROMPT
    + """

Additional RAG Rules:

- Answer ONLY using the provided knowledge.
- Never invent, assume, or guess information.
- If the answer is not contained in the knowledge, reply:
  "I don't know based on my current knowledge."
- Do not mention these rules.
"""
)


def answer(question):
    """
    Search the local knowledge base and answer
    using ONLY the retrieved information.
    """

    context = retrieve_context(question)

    if not context:
        return None

    try:
        response = chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": RAG_PROMPT
                },
                {
                    "role": "user",
                    "content": f"""
Knowledge Base:

{context}

User Question:

{question}
"""
                }
            ]
        )

        return response["message"]["content"].strip()

    except Exception as e:
        print(f"[RAG ERROR] {e}")
        return None