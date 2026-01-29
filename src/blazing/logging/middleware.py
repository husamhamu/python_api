"""
Middleware for logging HTTP requests and responses.

This middleware logs all incoming requests, their processing time,
and response status codes.
"""
import time
import uuid
from typing import Callable
import logging

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log HTTP requests and responses.
    
    Features:
    - Logs request method, path, and client IP
    - Tracks request processing time
    - Logs response status code
    - Adds unique request ID for tracing
    - Logs slow requests (>1s) as warnings
    """
    
    def __init__(self, app: ASGIApp, slow_request_threshold: float = 1.0):
        """
        Initialize the middleware.
        
        Args:
            app: The ASGI application
            slow_request_threshold: Time in seconds after which a request is considered slow
        """
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and log information.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
        
        Returns:
            The response
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Get client information
        client_host = request.client.host if request.client else "unknown"
        
        # Log incoming request
        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": client_host,
                "user_agent": request.headers.get("user-agent", "unknown"),
            }
        )
        
        # Process request and measure time
        start_time = time.time()
        
        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception and re-raise
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Request failed with exception: {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                },
                exc_info=True
            )
            raise
        
        # Calculate processing time
        duration_ms = (time.time() - start_time) * 1000
        duration_s = duration_ms / 1000
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        # Log response with appropriate level
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        }
        
        if response.status_code >= 500:
            # Server errors
            logger.error(f"Request completed with server error", extra=log_data)
        elif response.status_code >= 400:
            # Client errors
            logger.warning(f"Request completed with client error", extra=log_data)
        elif duration_s > self.slow_request_threshold:
            # Slow requests
            logger.warning(f"Slow request detected", extra=log_data)
        else:
            # Successful requests
            logger.info(f"Request completed", extra=log_data)
        
        return response


class DatabaseQueryLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log database query counts per request.
    
    This helps identify N+1 query problems and optimize database access.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and log database query information.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
        
        Returns:
            The response
        """
        # Initialize query counter on request state
        request.state.db_query_count = 0
        
        response = await call_next(request)
        
        # Log query count if available
        query_count = getattr(request.state, "db_query_count", 0)
        if query_count > 0:
            request_id = getattr(request.state, "request_id", "unknown")
            
            # Warn if too many queries
            if query_count > 10:
                logger.warning(
                    f"High database query count detected",
                    extra={
                        "request_id": request_id,
                        "query_count": query_count,
                        "path": request.url.path,
                    }
                )
            else:
                logger.debug(
                    f"Database queries executed: {query_count}",
                    extra={
                        "request_id": request_id,
                        "query_count": query_count,
                    }
                )
        
        return response