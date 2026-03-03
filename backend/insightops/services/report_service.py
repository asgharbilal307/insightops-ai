import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from insightops.models.incident import Incident


def generate_summary(db: Session):
    incidents = db.query(Incident).all()

    if not incidents:
        return {"message": "No incidents found"}

    data = [
        {
            "sentiment": i.sentiment,
            "confidence": float(i.confidence)
        }
        for i in incidents
    ]

    # Create DataFrame (Pandas usage)
    df = pd.DataFrame(data)

    total_incidents = len(df)

    sentiment_counts = df["sentiment"].value_counts().to_dict()

    average_confidence = np.mean(df["confidence"])
    std_confidence = np.std(df["confidence"])

    return {
        "total_incidents": total_incidents,
        "sentiment_distribution": sentiment_counts,
        "average_confidence": round(float(average_confidence), 4),
        "confidence_std_deviation": round(float(std_confidence), 4)
    }