from transformers import pipeline

classifier = pipeline(
    "text-classification",
    model="distilbert-base-uncased-finetuned-sst-2-english"
)


def analyze_sentiment(text: str):
    result = classifier(text)[0]

    return {
        "label": result["label"],
        "score": result["score"]
    }