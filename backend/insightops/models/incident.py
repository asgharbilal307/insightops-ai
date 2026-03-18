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