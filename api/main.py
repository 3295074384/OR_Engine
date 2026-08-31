import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router

app = FastAPI(title="OR Engine API", version="2.0.0")

# CORS: allow explicit origins via CORS_ORIGINS env (comma-separated),
# fall back to "*" (any) when not configured. Set allow_credentials=True so
# credentialed frontend requests are permitted.
cors_origins = os.environ.get("CORS_ORIGINS", "*")
allow_origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()] or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
