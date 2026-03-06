from fastapi import FastAPI
from insightops.db.database import engine
from insightops.models.incident import Incident
from fastapi.security import OAuth2PasswordBearer
from insightops.api.health import router as health_router
from insightops.api.ai import router as ai_router
from insightops.api.reports import router as report_router
from insightops.api.auth import router as auth_router
app = FastAPI(title="InsightOps AI")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

Incident.metadata.create_all(bind=engine)
app.include_router(health_router)
app.include_router(ai_router)
app.include_router(report_router)
app.include_router(auth_router)