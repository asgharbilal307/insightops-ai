from sqlalchemy import Column, Integer, String, Text
from insightops.db.database import Base

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    input_text = Column(Text)
    sentiment = Column(String)
    confidence = Column(String)
