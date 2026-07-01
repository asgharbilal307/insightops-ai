from transformers import pipeline
from sentence_transformers import SentenceTransformer, util
import faiss
import numpy as np

# =========================
# MODELS
# =========================

sentiment_model = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment-latest"
)

summary_model = pipeline(
    "summarization",
    model="facebook/bart-large-cnn"
)

classifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli"
)

qa_model = pipeline(
    "question-answering",
    model="distilbert-base-cased-distilled-squad"
)

similarity_model = SentenceTransformer('all-MiniLM-L6-v2')

# =========================
# LABELS
# =========================

labels = [
    "Billing",
    "Delivery",
    "Outage",
    "Fraud",
    "Other"
]

# =========================
# FAISS SETUP
# =========================

dimension = 384
faiss_index = faiss.IndexFlatL2(dimension)
faiss_texts = []

# =========================
# SAFE HELPERS
# =========================

def is_valid_text(text):
    return isinstance(text, str) and text.strip() != ""

# =========================
# SIMILARITY SEARCH
# =========================

def find_similar_incidents(text: str, incidents: list[str]):

    if not is_valid_text(text) or not incidents:
        return []

    clean_incidents = [i for i in incidents if is_valid_text(i)]

    if not clean_incidents:
        return []

    embeddings = similarity_model.encode([text] + clean_incidents)

    query_embedding = embeddings[0]
    incident_embeddings = embeddings[1:]

    scores = util.cos_sim(query_embedding, incident_embeddings)[0]

    similar = []

    for i, score in enumerate(scores):

        score_value = float(score)

        if score_value > 0.5:
            similar.append({
                "incident": clean_incidents[i],
                "similarity_score": round(score_value, 3)
            })

    return similar

# =========================
# QA
# =========================

def answer_question(context: str, question: str):

    if not is_valid_text(context) or not is_valid_text(question):
        return "No answer found."

    try:
        result = qa_model(question=question, context=context)
        return result["answer"]
    except:
        return "Unable to answer question."

# =========================
# CLASSIFICATION
# =========================

def classify_incident(text: str):

    if not is_valid_text(text):
        return "Other"

    try:
        result = classifier(text, labels)
        top_label = result["labels"][0]
        top_score = result["scores"][0]

        if top_score < 0.40:
            return "Uncertain"

        return top_label

    except:
        return "Other"

# =========================
# SEVERITY DETECTION
# =========================

def detect_severity(text: str):

    if not is_valid_text(text):
        return "LOW"

    text = text.lower()
    score = 0

    critical_words = [
        "security breach", "data leak", "production outage",
        "system failure", "database lost", "service unavailable"
    ]

    high_words = [
        "timeout", "high latency", "payment failed",
        "api failure", "server overload"
    ]

    medium_words = [
        "slow", "delay", "lag",
        "minor issue", "performance issue"
    ]

    for word in critical_words:
        if word in text:
            score += 5

    for word in high_words:
        if word in text:
            score += 3

    for word in medium_words:
        if word in text:
            score += 1

    if score >= 5:
        return "CRITICAL"
    elif score >= 3:
        return "HIGH"
    elif score >= 1:
        return "MEDIUM"
    return "LOW"

# =========================
# SMART SUMMARIZATION
# =========================

def should_summarize(text: str):

    text = text.lower()

    keywords = [
        "error", "issue", "incident", "outage",
        "failure", "bug", "crash", "exception"
    ]

    return any(k in text for k in keywords)

def summarize_text(text: str):

    if not is_valid_text(text):
        return ""

    word_count = len(text.split())

    if word_count < 30:
        return text

    try:
        max_len = min(60, word_count)
        min_len = min(20, max_len // 2)

        result = summary_model(
            text,
            max_length=max_len,
            min_length=min_len,
            do_sample=False
        )

        return result[0]["summary_text"]

    except:
        return text


def analyze_sentiment(text: str):

    if not is_valid_text(text):
        return {
            "label": "NEUTRAL",
            "score": 0.0,
            "severity": "LOW",
            "category": "Other",
            "summary": ""
        }

    try:
        sentiment = sentiment_model(text)[0]
        # Map the labels to readable format
        label_mapping = {
            "positive": "POSITIVE",
            "negative": "NEGATIVE",
            "neutral": "NEUTRAL"
        }
        sentiment["label"] = label_mapping.get(sentiment["label"], "NEUTRAL")
    except:
        sentiment = {"label": "NEUTRAL", "score": 0.0}

    severity = detect_severity(text)
    category = classify_incident(text)

    summary = text

    if should_summarize(text) and len(text.split()) > 30:
        summary = summarize_text(text)

    return {
        "label": sentiment["label"],
        "score": round(float(sentiment["score"]), 3),
        "severity": severity,
        "category": category,
        "summary": summary
    }

# =========================
# MEDIA SENTIMENT ANALYSIS
# =========================

def analyze_image_sentiment(image_label: str, label_confidence: float):
    if not is_valid_text(image_label):
        return {
            "label": "NEUTRAL",
            "score": 0.0,
            "severity": "LOW",
            "category": "Image",
            "summary": "No image label available."
        }

    try:
        sentiment = sentiment_model(image_label)[0]
        # Map the labels to readable format
        label_mapping = {
            "positive": "POSITIVE",
            "negative": "NEGATIVE",
            "neutral": "NEUTRAL"
        }
        sentiment["label"] = label_mapping.get(sentiment["label"], "NEUTRAL")
    except:
        sentiment = {"label": "NEUTRAL", "score": 0.0}

    severity = detect_severity(image_label)
    category = "Image"
    summary = image_label
    score = round(float(label_confidence), 3)

    return {
        "label": sentiment["label"],
        "score": score,
        "severity": severity,
        "category": category,
        "summary": summary
    }


def analyze_audio_sentiment(transcription: str, emotion: str):
    if is_valid_text(transcription):
        result = analyze_sentiment(transcription)
        result["category"] = "Audio"
        result["summary"] = transcription if len(transcription.split()) <= 60 else result["summary"]
        return result

    sentiment_label = "NEUTRAL"
    score = 0.5
    severity = "LOW"

    if emotion == "HIGH_URGENCY":
        sentiment_label = "NEGATIVE"
        score = 0.95
        severity = "HIGH"
    elif emotion == "MEDIUM_URGENCY":
        sentiment_label = "NEGATIVE"
        score = 0.80
        severity = "MEDIUM"
    elif emotion == "LOW_URGENCY":
        sentiment_label = "NEUTRAL"
        score = 0.45
        severity = "LOW"

    return {
        "label": sentiment_label,
        "score": round(score, 3),
        "severity": severity,
        "category": "Audio",
        "summary": transcription or f"Audio urgency: {emotion}"
    }

# =========================
# FAISS FUNCTIONS
# =========================

def add_incident_to_faiss(text: str):

    if not is_valid_text(text):
        return

    emb = similarity_model.encode([text])[0]
    emb = np.array([emb], dtype=np.float32)

    faiss_index.add(emb)
    faiss_texts.append(text)

# =========================
# SEARCH FAISS
# =========================

def search_similar_faiss(query_text: str, top_k=5):

    if not is_valid_text(query_text) or len(faiss_texts) == 0:
        return []

    query_emb = similarity_model.encode([query_text])[0]
    query_emb = np.array([query_emb], dtype=np.float32)

    D, I = faiss_index.search(query_emb, top_k)

    results = []

    for idx, dist in zip(I[0], D[0]):

        if idx == -1 or idx >= len(faiss_texts):
            continue

        similarity_score = 1 / (1 + dist)

        results.append({
            "incident": faiss_texts[idx],
            "score": round(float(similarity_score), 3)
        })

    return results

# =========================
# LOAD INCIDENTS SAFELY
# =========================

def load_existing_incidents(incident_list: list[str]):

    if not incident_list:
        return

    for text in incident_list:
        if is_valid_text(text):
            add_incident_to_faiss(text)