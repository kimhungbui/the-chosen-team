"""
FastAPI Server Application — Proposal Scorer.
Runnable standalone server for handling HTTP API requests from any frontend (React, Next.js, Streamlit, etc.).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.router import router as api_v1_router

app = FastAPI(
    title="Proposal Scorer & Auditor API",
    description="FPT Software Europe — Automated Pre-Sales Quality & RFP Compliance Auditor API Contract",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for external frontend integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.server:app", host="0.0.0.0", port=8000, reload=True)
