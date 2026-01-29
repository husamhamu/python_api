"""
Main application module with logging configuration.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from blazing.db import create_db_and_tables
from blazing.routes import pokemon
from blazing.logging.logging_config import setup_logging, get_logger
from blazing.logging.middleware import (
    RequestLoggingMiddleware,
    DatabaseQueryLoggingMiddleware,
)

# Initialize logging
log_level = os.getenv("LOG_LEVEL", "INFO")
enable_json_logs = os.getenv("LOG_JSON", "false").lower() == "true"
enable_file_logs = os.getenv("LOG_FILE", "true").lower() == "true"

setup_logging(
    log_level=log_level,
    enable_json_logs=enable_json_logs,
    enable_file_logs=enable_file_logs,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    logger.info("Starting Blazing Pokemon API")
    logger.info(f"Log level: {log_level}")
    logger.info(f"JSON logging: {enable_json_logs}")

    try:
        create_db_and_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}", exc_info=True)
        raise

    logger.info("Application startup complete")

    yield

    logger.info("Shutting down Blazing Pokemon API")


app = FastAPI(
    title="Blazing Pokemon API",
    description="A professional Pokemon management API",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware
app.add_middleware(RequestLoggingMiddleware, slow_request_threshold=1.0)
app.add_middleware(DatabaseQueryLoggingMiddleware)

# Include routers
app.include_router(pokemon.router)

logger.info("Routes registered successfully")


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Health status
    """
    logger.debug("Health check called")
    return {"status": "healthy", "service": "blazing-pokemon-api", "version": "0.1.0"}


@app.get("/")
async def root():
    """
    Root endpoint.

    Returns:
        dict: Welcome message
    """
    logger.debug("Root endpoint called")
    return {
        "message": "Welcome to Blazing Pokemon API",
        "docs": "/docs",
        "health": "/health",
    }
