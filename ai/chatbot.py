from ollama import chat
from ai.memory import messages

def ask(question):
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