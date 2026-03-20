from transformers import pipeline
from sentence_transformers import SentenceTransformer, util
import faiss
import numpy as np

sentiment_model = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
summary_model = pipeline("summarization",model="facebook/bart-large-cnn")
classifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli"
)
qa_model = pipeline("question-answering")
similarity_model = SentenceTransformer('all-MiniLM-L6-v2')

labels = ["Billing", "Delivery", "Outage", "Fraud", "Other"]

dimension = 384  # embedding size of all-MiniLM-L6-v2
faiss_index = faiss.IndexFlatL2(dimension)
faiss_texts = []

def find_similar_incidents(text: str, incidents: list[str]):

    if not text or not incidents:
        return []

    embeddings = similarity_model.encode([text] + incidents)
    query_embedding = embeddings[0]
    incident_embeddings = embeddings[1:]

    scores = util.cos_sim(query_embedding, incident_embeddings)[0]

    similar = []

    for i, score in enumerate(scores):
        if score > 0.5:  # threshold for similarity
            similar.append((incidents[i], float(score)))

    return similar

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

def add_incident_to_faiss(text: str):
    emb = similarity_model.encode([text])[0]
    faiss_index.add(np.array([emb], dtype=np.float32))
    faiss_texts.append(text)  # MUST match index order

def search_similar_faiss(query_text: str, top_k=5):
    if len(faiss_texts) == 0:
        return []  # no data yet

    query_emb = similarity_model.encode([query_text])[0]
    D, I = faiss_index.search(
        np.array([query_emb], dtype=np.float32), top_k
    )

    results = []

    for idx, dist in zip(I[0], D[0]):

        # ✅ skip invalid indices
        if idx == -1:
            continue

        # ✅ prevent out-of-range access
        if idx >= len(faiss_texts):
            continue

        score = 1 / (1 + dist)
        results.append((faiss_texts[idx], score))

    return results
def load_existing_incidents(incident_list: list[str]):

    for text in incident_list:
        add_incident_to_faiss(text)