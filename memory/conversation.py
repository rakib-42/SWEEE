from collections import deque


class ConversationMemory:
    def __init__(self, max_messages=30):
        self.history = deque(maxlen=max_messages)

    def add(self, role, content):
        self.history.append({
            "role": role,
            "content": content
        })

    def add_user(self, message):
        self.add("user", message)

    def add_assistant(self, message):
        self.add("assistant", message)

    def add_system(self, message):
        self.add("system", message)

    def get_history(self):
        return list(self.history)

    def last_message(self):
        if self.history:
            return self.history[-1]
        return None

    def last_user_message(self):
        for message in reversed(self.history):
            if message["role"] == "user":
                return message["content"]
        return None

    def clear(self):
        self.history.clear()

    def size(self):
        return len(self.history)