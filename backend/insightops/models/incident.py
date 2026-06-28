from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey,DateTime
from sqlalchemy.sql import func
from insightops.db.database import Base
from typing import Optional

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)

    text = Column(Text)

    sentiment = Column(String)

    confidence = Column(Float)

    user_id = Column(Integer, ForeignKey("users.id"))

    severity = Column(String)

    summary= Column(String)

    category = Column(String)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Image analysis fields
    extracted_text = Column(Text, nullable=True)
    image_label = Column(String, nullable=True)
    image_confidence = Column(Float, nullable=True)

    # Audio analysis fields
    audio_transcription = Column(Text, nullable=True)
    audio_emotion = Column(String, nullable=True)

    # Analysis type field
    analysis_type = Column(String, nullable=True, default="text")