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

@router.get("/trend")
def incident_trend(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    incidents = db.query(Incident).filter(
        Incident.user_id == current_user.id
    ).all()

    total = len(incidents)

    critical = len([i for i in incidents if i.severity == "CRITICAL"])
    high = len([i for i in incidents if i.severity == "HIGH"])

    if critical >= 5 or high >= 7:
        system_status = "UNSTABLE"
    elif critical >= 2:
        system_status = "WARNING"
    else:
        system_status = "STABLE"

    return {
        "total_incidents": total,
        "critical_incidents": critical,
        "high_incidents": high,
        "system_status": system_status
    }

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

@router.get("/dashboard")
def dashboard_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    incidents = db.query(Incident).filter(
        Incident.user_id == current_user.id
    ).all()

    severity_counts = {
        "CRITICAL": 0,
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0
    }

    sentiment_counts = {
        "POSITIVE": 0,
        "NEGATIVE": 0
    }

    for incident in incidents:
        if incident.severity in severity_counts:
            severity_counts[incident.severity] += 1

        if incident.sentiment in sentiment_counts:
            sentiment_counts[incident.sentiment] += 1

    return {
        "severity_distribution": severity_counts,
        "sentiment_distribution": sentiment_counts,
        "total_incidents": len(incidents)
    }