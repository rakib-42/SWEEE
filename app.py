from ollama import chat

print("=" * 50)
print("SWEEE - Software Engineering Educational Expert")
print("Type 'exit' to quit.")
print("=" * 50)

while True:
    user = input("\nYou: ")

    if user.lower() == "exit":
        print("SWEEE: Goodbye!")
        break

    response = chat(
        model="qwen2.5:1.5b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are SWEEE (Software Engineering Educational Expert), "
                    "an AI-powered departmental assistant robot for the Software Engineering Department. "
                    "Be polite, concise, and helpful."
                ),
            },
            {
                "role": "user",
                "content": user,
            },
        ],
    )

    print("\nSWEEE:", response["message"]["content"])