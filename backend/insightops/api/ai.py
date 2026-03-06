from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from insightops.db.deps import get_db
from insightops.models.incident import Incident
from insightops.models.user import User
from insightops.schemas.incident import AnalyzeRequest, AnalyzeResponse
from insightops.services.ai_service import analyze_sentiment
from insightops.core.security import get_current_user

router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_text(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    result = analyze_sentiment(request.text)

    new_incident = Incident(
        text=request.text,
        sentiment=result["label"],
        confidence=result["score"],
        user_id=current_user.id  # 🔥 user-specific
    )

    db.add(new_incident)
    db.commit()
    db.refresh(new_incident)

    return AnalyzeResponse(
        id=new_incident.id,
        text=new_incident.text,
        sentiment=new_incident.sentiment,
        confidence=new_incident.confidence
    )


@router.get("/incidents")
def get_incidents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    incidents = db.query(Incident).filter(
        Incident.id == current_user.id
    ).all()

    return incidents