class KnowledgeResult:
    def __init__(
        self,
        found=False,
        answer=None,
        source=None,
        confidence=0.0,
        data=None
    ):
        self.found = found
        self.answer = answer
        self.source = source
        self.confidence = confidence
        self.data = data

    def to_dict(self):
        return {
            "found": self.found,
            "answer": self.answer,
            "source": self.source,
            "confidence": self.confidence,
            "data": self.data
        }