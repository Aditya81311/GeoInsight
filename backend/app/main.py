from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import environment

app = FastAPI(
    title=settings.app_name,
    description="Geospatial Intelligence API for Kamrup District, Assam.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(environment.router)


@app.get("/")
def root():
    return {
        "service": settings.app_name,
        "status": "ok",
        "docs": "/docs",
        "example": f"{settings.api_v1_prefix}/environment?district=kamrup&month=2026-06",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
