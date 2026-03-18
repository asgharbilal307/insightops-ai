from transformers import pipeline

sentiment_model = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
summary_model = pipeline("summarization",model="facebook/bart-large-cnn")
classifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli"
)
qa_model = pipeline("question-answering")
labels = ["Billing", "Delivery", "Outage", "Fraud", "Other"]

def answer_question(context: str, question: str):
    result = qa_model(question=question, context=context)
    return result["answer"]

def classify_incident(text: str):

    result = classifier(text, labels)

    return result["labels"][0]  # top category

def detect_severity(text: str):

    text = text.lower()

    if "crash" in text or "down" in text:
        return "CRITICAL"
    if "error" in text or "failed" in text:
        return "HIGH"
    if "slow" in text:
        return "MEDIUM"

    return "LOW"


def summarize_text(text: str):

    try:
        result = summary_model(
            text,
            max_length=50,
            min_length=20,
            do_sample=False
        )

        return result[0]["summary_text"]

    except Exception:
        return text  # fallback


def analyze_sentiment(text: str):

    sentiment = sentiment_model(text)[0]

    severity = detect_severity(text)

    category = classify_incident(text)


    summary = summarize_text(text)
    if not summary:
        summary = text

    return {
        "label": sentiment["label"],
        "score": sentiment["score"],
        "severity": severity,
        "category": category,
        "summary": summary
    }