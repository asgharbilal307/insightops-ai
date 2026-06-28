from insightops.services.forecast_services import generate_forecast
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
    incidents = db.query(Incident).filter(Incident.user_id == current_user.id).all()
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
def dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    incidents = db.query(Incident).filter(
        Incident.user_id == current_user.id
    ).all()

    total_incidents = len(incidents)

    critical_incidents = 0
    high_incidents = 0
    medium_incidents = 0

    categories = {}

    def _incident_risk_level(incident):
        sentiment = (incident.sentiment or "").upper()

        try:
            confidence = float(incident.confidence)
        except:
            confidence = 0.5

        if incident.severity == "CRITICAL":
            return "CRITICAL"
        if incident.severity == "HIGH":
            return "HIGH"

        if sentiment == "NEGATIVE":
            if confidence >= 0.90:
                return "CRITICAL"
            elif confidence >= 0.75:
                return "HIGH"
            return "MEDIUM"

        if sentiment == "POSITIVE":
            return "MEDIUM"

        return "MEDIUM"

    for incident in incidents:
        risk_level = _incident_risk_level(incident)

        if risk_level == "CRITICAL":
            critical_incidents += 1
        elif risk_level == "HIGH":
            high_incidents += 1
        else:
            medium_incidents += 1

        category_key = incident.category or incident.analysis_type or "Other"
        categories[category_key] = categories.get(category_key, 0) + 1

    # -----------------------------------------
    # AI RISK SCORE
    # -----------------------------------------

    if total_incidents == 0:
        risk_score = 0
    else:
        critical_percent = (critical_incidents / total_incidents) * 60
        high_percent = (high_incidents / total_incidents) * 30
        medium_percent = (medium_incidents / total_incidents) * 10
        risk_score = int(critical_percent + high_percent + medium_percent)

    # -----------------------------------------
    # TREND ANALYSIS
    # -----------------------------------------

    trend = "Stable"

    if critical_incidents >= 7:
        trend = "High Risk"

    elif high_incidents >= 3:
        trend = "Moderate Risk"

    # -----------------------------------------
    # RESPONSE
    # -----------------------------------------

    return {
        "total_incidents": total_incidents,
        "critical_incidents": critical_incidents,
        "high_incidents": high_incidents,
        "medium_incidents": medium_incidents,
        "risk_score": risk_score,
        "trend": trend,
        "categories": categories
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



@router.get("/forecast")
def forecast_incidents(
    db: Session = Depends(get_db)
):


    result = generate_forecast(db)

    return result