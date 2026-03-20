from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class IncidentBase(BaseModel):
    title: str
    description: str
    severity: str
    status: str

class IncidentCreate(IncidentBase):
    pass

class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None

class IncidentResponse(IncidentBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
class AnalyzeRequest(BaseModel):
    text: str


class AnalyzeResponse(BaseModel):
    id: int
    text: str
    category: str
    sentiment: str
    severity: str
    confidence: float
    summary:str

    class Config:
        from_attributes = True

class QARequest(BaseModel):
    context: str
    question: str

# Response for Q&A
class QAResponse(BaseModel):
    question: str
    answer: str
    context: str

class SimilarIncidentsRequest(BaseModel):
    text: str
    incidents: list[str]  # List of existing incidents to compare against

class SimilarIncidentsResponse(BaseModel):
    text: str
    similar_incidents: list[dict]
