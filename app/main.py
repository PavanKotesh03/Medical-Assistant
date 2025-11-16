"""
Main FastAPI application
Entry point for the Medical Symptom Assistant API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import diagnose, symptoms, diseases

# Create FastAPI application
app = FastAPI(
    title="Medical Symptom Assistant API",
    description="API for diagnosing diseases based on symptoms using PostgreSQL stored procedures",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc UI
)

# Add CORS middleware (allows frontend to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(diagnose.router, prefix="/api")
app.include_router(symptoms.router, prefix="/api")
app.include_router(diseases.router, prefix="/api")


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API health check
    """
    return {
        "status": "online",
        "message": "Medical Symptom Assistant API is running",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "diagnose": "/api/diagnose",
            "symptoms": "/api/symptoms",
            "diseases": "/api/diseases"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "service": "Medical Symptom Assistant API"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)