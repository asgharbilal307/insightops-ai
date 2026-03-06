from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import pandas as pd
import numpy as np

from insightops.db.deps import get_db
from insightops.models.incident import Incident
from insightops.models.user import User
from insightops.core.security import get_current_user

router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)

@router.get("/summary")
def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Fetch incidents for the current user
    incidents = db.query(Incident).filter(Incident.id == current_user.id).all()
    if not incidents:
        return {"message": "No incidents found"}

    # Prepare data
    data = [{"sentiment": i.sentiment, "confidence": float(i.confidence)} for i in incidents]
    df = pd.DataFrame(data)

    # Statistics
    total_incidents = len(df)
    sentiment_distribution = df["sentiment"].value_counts().to_dict()
    average_confidence = np.mean(df["confidence"])
    std_confidence = np.std(df["confidence"])

    return {
        "total_incidents": total_incidents,
        "sentiment_distribution": sentiment_distribution,
        "average_confidence": round(float(average_confidence), 4),
        "confidence_std_deviation": round(float(std_confidence), 4)
    }