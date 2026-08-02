from ai.chatbot import ask
from speech.sound import play_startup
from speech.idle_sound import start_idle_sound

play_startup()

start_idle_sound()

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