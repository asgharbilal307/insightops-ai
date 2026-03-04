from fastapi import FastAPI
from insightops.db.database import engine
from insightops.models.incident import Incident
from insightops.api.health import router as health_router
from insightops.api.ai import router as ai_router
from insightops.api.reports import router as report_router
from insightops.api import auth
app = FastAPI(title="InsightOps AI")
Incident.metadata.create_all(bind=engine)
app.include_router(health_router)
app.include_router(ai_router)
app.include_router(report_router)
app.include_router(auth.router)