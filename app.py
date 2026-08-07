from ai.chatbot import ask
from speech.listener import listen
from speech.sound import play_startup
from speech.idle_sound import start_idle_sound
from speech.voice import speak

play_startup()

start_idle_sound()

print("=" * 50)
print("      SWEEE - AI Department Assistant")
print("=" * 50)

while True:
    user = listen()

    if user.lower() in ["exit", "quit"]:
        print("\nGoodbye!")
        break

    reply = ask(user)

    print(f"\nSWEEE: {reply}")
    speak(reply)