"""
FastAPI Application Entry Point

Week 2 Day 2: FastAPI Skeleton Setup
"""

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# TODO: Import your API routers when created
# from app.api import definitions, validation, health

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="DefinitieAgent API",
    description="Nederlandse juridische definitiegenerator met 46 validatieregels",
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS configuration (for React frontend if Week 7+)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv(
        "CORS_ORIGINS", "http://localhost:8501,http://localhost:3000"
    ).split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
    }


# TODO: Register API routers
# app.include_router(definitions.router, prefix="/api/definitions", tags=["definitions"])
# app.include_router(validation.router, prefix="/api/validation", tags=["validation"])
# app.include_router(health.router, prefix="/api", tags=["health"])


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting DefinitieAgent API v3.0.0")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")

    # TODO: Initialize database connection
    # TODO: Initialize Redis cache
    # TODO: Initialize AI service
    # TODO: Load validation rules

    logger.info("Startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down DefinitieAgent API")

    # TODO: Close database connections
    # TODO: Close Redis connections

    logger.info("Shutdown complete")


# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "DefinitieAgent API v3.0.0",
        "docs": "/api/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
