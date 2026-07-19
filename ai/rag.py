from ollama import chat


def answer_from_context(question, context):
    response = chat(
        model="qwen2.5:1.5b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are SWEEE.\n"
                    "Answer ONLY using the information provided.\n"
                    "If the information is insufficient, say you don't know.\n"
                    "Do not make up facts."
                )
            },
            {
                "role": "user",
                "content": f"""
Information:
{context}

Question:
{question}
"""
            }
        ]
    )

    return response["message"]["content"]