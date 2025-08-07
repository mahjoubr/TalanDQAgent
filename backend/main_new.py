"""
Main FastAPI application for Data Quality Pipeline
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routes import router

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Data Quality Pipeline API",
    version="1.0.0",
    description="Comprehensive data quality analysis and Power BI integration platform"
)

# Enable CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routes
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
