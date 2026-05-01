from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi import UploadFile, File
import os

from insightops.services.multimodel_service import (
    analyze_image,
    transcribe_audio,
    detect_audio_emotion,
    multimodal_analysis
)
from insightops.services.forecast_services import generate_forecast
from insightops.db.deps import get_db
from insightops.models.incident import Incident
from insightops.models.user import User
from insightops.schemas.incident import AnalyzeRequest, AnalyzeResponse,QARequest,QAResponse,SimilarIncidentsRequest,SimilarIncidentsResponse
from insightops.services.ai_service import analyze_sentiment,answer_question,find_similar_incidents,add_incident_to_faiss,search_similar_faiss
from insightops.core.security import get_current_user

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
    dependencies=[Depends(get_current_user)]
)


@router.post("/similar-incidents", response_model=SimilarIncidentsResponse)
def similar_incidents(request: SimilarIncidentsRequest):
    similar = find_similar_incidents(request.text, request.incidents)

    # convert to list of dicts
    similar_list = [{"incident": inc, "score": score} for inc, score in similar]

    return SimilarIncidentsResponse(
        text=request.text,
        similar_incidents=similar_list
    )

@router.post("/question", response_model=QAResponse)
def ask_question(request: QARequest):
    answer = answer_question(request.context, request.question)

    return QAResponse(
        question=request.question,
        answer=answer,
        context=request.context
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
        severity=result["severity"],
        category=result["category"],
        confidence=result["score"],
        summary=result.get("summary") or request.text,
        user_id=current_user.id
    )

    db.add(new_incident)
    db.commit()
    db.refresh(new_incident)
    add_incident_to_faiss(request.text)

    return AnalyzeResponse(
        id=new_incident.id,
        text=new_incident.text,
        sentiment=new_incident.sentiment,
        category=new_incident.category,
        severity=new_incident.severity,
        confidence=new_incident.confidence,
        summary=new_incident.summary
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

@router.post("/similar-faiss", response_model=SimilarIncidentsResponse)
def faiss_endpoint(request: SimilarIncidentsRequest):

    results = search_similar_faiss(request.text)

    return SimilarIncidentsResponse(
        text=request.text,
        similar_incidents=[
            {"incident": inc, "score": float(score)} for inc, score in results
        ]
    )

@router.post("/analyze/image")
def analyze_image_endpoint(
    file: UploadFile = File(...)
):

    file_path = f"temp_{file.filename}"

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    result = analyze_image(file_path)

    os.remove(file_path)

    return result

@router.post("/analyze/audio")

def analyze_audio_endpoint(
    file: UploadFile = File(...)
):

    file_path = f"temp_{file.filename}"

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    transcription = transcribe_audio(file_path)

    emotion = detect_audio_emotion(file_path)

    os.remove(file_path)

    return {
        "transcription": transcription,
        "emotion": emotion
    }

@router.post("/analyze/multimodal")
def multimodal_endpoint(
    text: str = None,
    image: UploadFile = File(None),
    audio: UploadFile = File(None)
):

    image_path = None
    audio_path = None

    # IMAGE
    if image:

        image_path = f"temp_{image.filename}"

        with open(image_path, "wb") as f:
            f.write(image.file.read())

    # AUDIO
    if audio:

        audio_path = f"temp_{audio.filename}"

        with open(audio_path, "wb") as f:
            f.write(audio.file.read())

    result = multimodal_analysis(
        text=text,
        image_path=image_path,
        audio_path=audio_path
    )

    if image_path and os.path.exists(image_path):
        os.remove(image_path)

    if audio_path and os.path.exists(audio_path):
        os.remove(audio_path)

    return result

@router.get("/forecast")
def forecast_incidents(
    db: Session = Depends(get_db)
):

    incidents = db.query(Incident).all()

    result = generate_forecast(incidents)

    return result