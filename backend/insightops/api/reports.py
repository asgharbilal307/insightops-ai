from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from insightops.db.deps import get_db
from insightops.services.report_service import generate_summary

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    return generate_summary(db)