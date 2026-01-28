from transformers import pipeline

class AIService:
    def __init__(self):
        self.classifier = pipeline(
            "text-classification",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )
        self.summarizer = pipeline(
            "text-generation",
            model="facebook/bart-large-cnn"
        )

    def analyze_text(self, text: str):
        result = self.classifier(text)
        return result
    def summarize_text(self, text: str):
        result = self.summarizer(text)
        return result