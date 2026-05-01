from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import pandas as pd
import numpy as np

from insightops.db.deps import get_db
from insightops.models.incident import Incident
from insightops.models.user import User
from insightops.core.security import get_current_user
from insightops.services.alert_service import generate_alerts
from insightops.services.trend_service import analyze_trends

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

@router.get("/alerts")
def get_alerts(
    db: Session = Depends(get_db)
):

    incidents = db.query(Incident).all()

    return generate_alerts(incidents)

@router.get("/trends")
def get_trends(
    db: Session = Depends(get_db)
):

    incidents = db.query(Incident).all()

    return analyze_trends(incidents)

@router.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db)
):

    incidents = db.query(Incident).all()

    total = len(incidents)

    critical = len([
        i for i in incidents
        if i.severity == "CRITICAL"
    ])

    high = len([
        i for i in incidents
        if i.severity == "HIGH"
    ])

    categories = {}

    for incident in incidents:

        if incident.category not in categories:
            categories[incident.category] = 0

        categories[incident.category] += 1

    return {
        "total_incidents": total,
        "critical_incidents": critical,
        "high_incidents": high,
        "categories": categories
    }