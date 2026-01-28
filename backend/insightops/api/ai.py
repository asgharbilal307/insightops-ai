from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from insightops.services.ai_service import AIService
from insightops.db.deps import get_db
from insightops.models.incident import Incident

router = APIRouter(prefix="/ai", tags=["AI"])
ai_service = AIService()

@router.post("/analyze")
def analyze_text(text: str, db: Session = Depends(get_db)):
    result = ai_service.analyze_text(text)[0]

    incident = Incident(
        input_text=text,
        sentiment=result["label"],
        confidence=str(result["score"])
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    return {
        "id": incident.id,
        "sentiment": incident.sentiment,
        "confidence": incident.confidence
    }

@router.get("/incidents")
def get_incidents(db: Session = Depends(get_db)):
    return db.query(Incident).all()
