"""
BHUMI-FUSION Backend Application
Problem Statement 26013: Automated Integration and Intelligent Harmonization of Multi-source Geospatial Data
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.endpoints import router as api_router
from backend.app.services.pipeline import pipeline

app = FastAPI(
    title="BHUMI-FUSION",
    description="AI-Powered Cadastral Reconciliation & Geospatial Harmonization Platform",
    version="1.0.0"
)

# Enable CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API endpoints
app.include_router(api_router)

@app.on_event("startup")
async def startup_event():
    """Ensure database has initial demo dataset ready for instant response."""
    try:
        pipeline.load_and_run_demo()
        print("BHUMI-FUSION engine initialized with demo cadastral dataset.")
    except Exception as e:
        print(f"Warning during startup demo loading: {e}")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "BHUMI-FUSION Cadastral Reconciliation Engine",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
