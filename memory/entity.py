class EntityMemory:

    def __init__(self):
        self.clear()

    def remember_teacher(self, teacher):
        self.teacher = teacher
        self.place = None
        self.followups = 1

    def remember_place(self, place):
        self.place = place
        self.teacher = None
        self.followups = 1

    def get_teacher(self):
        if self.teacher and self.followups > 0:
            self.followups -= 1
            return self.teacher
        return None

    def get_place(self):
        if self.place and self.followups > 0:
            self.followups -= 1
            return self.place
        return None

    def clear(self):
        self.teacher = None
        self.place = None
        self.followups = 0