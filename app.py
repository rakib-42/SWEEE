from ai.chatbot import ask

print("=" * 50)
print("      SWEEE - AI Department Assistant")
print("=" * 50)

while True:
    user = input("\nYou: ")

    if user.lower() in ["exit", "quit"]:
        print("\nGoodbye!")
        break

    reply = ask(user)

    print(f"\nSWEEE: {reply}")