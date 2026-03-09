from transformers import pipeline

sentiment_model = pipeline("sentiment-analysis")


def detect_severity(text: str):

    text = text.lower()

    if "crash" in text or "down" in text or "failure" in text:
        return "CRITICAL"

    if "error" in text or "failed" in text:
        return "HIGH"

    if "slow" in text or "delay" in text:
        return "MEDIUM"

    return "LOW"


def analyze_sentiment(text: str):

    result = sentiment_model(text)[0]

    severity = detect_severity(text)

    return {
        "label": result["label"],
        "score": result["score"],
        "severity": severity
    }