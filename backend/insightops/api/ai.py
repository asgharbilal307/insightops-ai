import os
import shutil
import tempfile

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from insightops.db.deps import get_db
from insightops.models.incident import Incident
from insightops.models.user import User
from insightops.core.security import get_current_user
from insightops.schemas.incident import AnalyzeRequest
from insightops.services.ai_service import (
    analyze_sentiment,
    analyze_image_sentiment,
    analyze_audio_sentiment,
)
from insightops.services.multimodel_service import (
    analyze_image,
    detect_audio_emotion,
    transcribe_audio,
    extract_text_from_image,
)

router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)


def save_upload_file(upload_file: UploadFile) -> str:
    suffix = os.path.splitext(upload_file.filename)[1] or ""
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)

    try:
        shutil.copyfileobj(upload_file.file, tmp_file)
    finally:
        tmp_file.close()

    return tmp_file.name


@router.post("/analyze")
def analyze_text(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    text = request.text.strip()

    if not text:
        raise HTTPException(status_code=400, detail="Text is required for analysis.")

    result = analyze_sentiment(text)

    incident = Incident(
        text=text,
        sentiment=result["label"],
        confidence=result["score"],
        severity=result["severity"],
        category=result["category"],
        summary=result["summary"],
        user_id=current_user.id,
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    return {
        "text": text,
        "category": result["category"],
        "sentiment": result["label"],
        "severity": result["severity"],
        "confidence": result["score"],
        "summary": result["summary"],
        "id": incident.id,
    }


@router.get("/incidents")
def get_incidents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    incidents = db.query(Incident).filter(
        Incident.user_id == current_user.id
    ).order_by(Incident.created_at.desc()).all()

    return [
        {
            "id": incident.id,
            "input_text": incident.text or incident.extracted_text or incident.audio_transcription or f"{incident.analysis_type} analysis",
            "severity": incident.severity or "MEDIUM",
            "sentiment": incident.sentiment,
            "category": incident.category,
            "summary": incident.summary,
            "analysis_type": incident.analysis_type or "text",
            "image_label": incident.image_label,
            "image_confidence": incident.image_confidence,
            "audio_emotion": incident.audio_emotion,
            "created_at": incident.created_at.isoformat() if incident.created_at else None,
        }
        for incident in incidents
    ]


@router.post("/analyze/image")
def analyze_image_route(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    file_path = save_upload_file(file)

    try:
        result = analyze_image(file_path)
        image_sentiment = analyze_image_sentiment(result["label"], result["confidence"])

        incident = Incident(
            image_label=result["label"],
            image_confidence=result["confidence"],
            sentiment=image_sentiment["label"],
            confidence=image_sentiment["score"],
            severity=image_sentiment["severity"],
            category=image_sentiment["category"],
            summary=image_sentiment["summary"],
            analysis_type="image",
            user_id=current_user.id,
        )
        
        db.add(incident)
        db.commit()
        db.refresh(incident)
        
        return {
            **result,
            "sentiment": image_sentiment["label"],
            "confidence": image_sentiment["score"],
            "severity": image_sentiment["severity"],
            "category": image_sentiment["category"],
            "summary": image_sentiment["summary"],
            "id": incident.id
        }
    finally:
        os.unlink(file_path)


@router.post("/extract-text")
def extract_text_route(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    file_path = save_upload_file(file)

    try:
        text = extract_text_from_image(file_path)
        
        incident = Incident(
            extracted_text=text,
            analysis_type="text_extraction",
            user_id=current_user.id,
        )
        
        db.add(incident)
        db.commit()
        db.refresh(incident)
        
        return {"extracted_text": text, "id": incident.id}
    finally:
        os.unlink(file_path)


@router.post("/analyze/audio")
def analyze_audio_route(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    file_path = save_upload_file(file)

    try:
        transcription = transcribe_audio(file_path)
        emotion = detect_audio_emotion(file_path)
        audio_sentiment = analyze_audio_sentiment(transcription, emotion)
        
        incident = Incident(
            audio_transcription=transcription,
            audio_emotion=emotion,
            sentiment=audio_sentiment["label"],
            confidence=audio_sentiment["score"],
            severity=audio_sentiment["severity"],
            category=audio_sentiment["category"],
            summary=audio_sentiment["summary"],
            analysis_type="audio",
            user_id=current_user.id,
        )
        
        db.add(incident)
        db.commit()
        db.refresh(incident)

        return {
            "transcription": transcription,
            "emotion": emotion,
            "sentiment": audio_sentiment["label"],
            "confidence": audio_sentiment["score"],
            "severity": audio_sentiment["severity"],
            "category": audio_sentiment["category"],
            "summary": audio_sentiment["summary"],
            "id": incident.id,
        }
    finally:
        os.unlink(file_path)


@router.post("/analyze/multimodal")
def analyze_multimodal_route(
    text: str = Form(None),
    image: UploadFile | None = File(None),
    audio: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not text and not image and not audio:
        raise HTTPException(
            status_code=400,
            detail="Provide text, image, or audio for multimodal analysis.",
        )

    response = {}

    if text:
        analysis = analyze_sentiment(text)
        response["text_analysis"] = analysis

        incident = Incident(
            text=text,
            sentiment=analysis["label"],
            confidence=analysis["score"],
            severity=analysis["severity"],
            category=analysis["category"],
            summary=analysis["summary"],
            user_id=current_user.id,
        )

        db.add(incident)
        db.commit()
        db.refresh(incident)

    if image:
        image_path = save_upload_file(image)

        try:
            image_result = analyze_image(image_path)
            image_sentiment = analyze_image_sentiment(image_result["label"], image_result["confidence"])
            response["image_analysis"] = {
                **image_result,
                "sentiment": image_sentiment["label"],
                "confidence": image_sentiment["score"],
                "severity": image_sentiment["severity"],
                "category": image_sentiment["category"],
                "summary": image_sentiment["summary"],
            }
            
            # Save image analysis to database
            image_incident = Incident(
                image_label=image_result["label"],
                image_confidence=image_result["confidence"],
                sentiment=image_sentiment["label"],
                confidence=image_sentiment["score"],
                severity=image_sentiment["severity"],
                category=image_sentiment["category"],
                summary=image_sentiment["summary"],
                analysis_type="image",
                user_id=current_user.id,
            )
            db.add(image_incident)
            db.commit()
        finally:
            os.unlink(image_path)

    if audio:
        audio_path = save_upload_file(audio)

        try:
            transcription = transcribe_audio(audio_path)
            emotion = detect_audio_emotion(audio_path)
            audio_sentiment = analyze_audio_sentiment(transcription, emotion)
            response["audio_analysis"] = {
                "transcription": transcription,
                "emotion": emotion,
                "sentiment": audio_sentiment["label"],
                "confidence": audio_sentiment["score"],
                "severity": audio_sentiment["severity"],
                "category": audio_sentiment["category"],
                "summary": audio_sentiment["summary"],
            }
            
            # Save audio analysis to database
            audio_incident = Incident(
                audio_transcription=transcription,
                audio_emotion=emotion,
                sentiment=audio_sentiment["label"],
                confidence=audio_sentiment["score"],
                severity=audio_sentiment["severity"],
                category=audio_sentiment["category"],
                summary=audio_sentiment["summary"],
                analysis_type="audio",
                user_id=current_user.id,
            )
            db.add(audio_incident)
            db.commit()
        finally:
            os.unlink(audio_path)

    return response
