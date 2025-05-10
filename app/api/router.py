from app.api.endpoints import health_metrics
from fastapi import APIRouter

api_router = APIRouter()

api_router.include_router(health_metrics.router, tags=["Health Metrics"])
