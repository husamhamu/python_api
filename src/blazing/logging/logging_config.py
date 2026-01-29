"""
Logging configuration for the Blazing Pokemon API.

This module sets up structured logging with rotation, different log levels,
and separate handlers for file and console output.
"""
import logging
import sys
import copy
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    Outputs logs in JSON format for easy parsing and analysis.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
            
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        
        return json.dumps(log_data)


class ColoredConsoleFormatter(logging.Formatter):
    """
    Colored formatter for console output.
    Makes logs easier to read during development.
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        # Create a shallow copy of the record so we don't modify the original
        # This prevents colors from leaking into file logs
        record_copy = copy.copy(record)
        
        # Apply color to the COPY, not the original record
        color = self.COLORS.get(record_copy.levelname, self.RESET)
        record_copy.levelname = f"{color}{record_copy.levelname}{self.RESET}"
        
        return super().format(record_copy)


def setup_logging(
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    enable_json_logs: bool = False,
    enable_file_logs: bool = True,
    app_name: str = "blazing"
) -> None:
    """
    Set up logging configuration for the application.
    
    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files. If None, uses ./logs
        enable_json_logs: Whether to use JSON formatting for file logs
        enable_file_logs: Whether to write logs to files
        app_name: Application name for log files
    
    Example:
        >>> setup_logging(log_level="DEBUG", enable_json_logs=True)
    """
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory if needed
    if enable_file_logs:
        if log_dir is None:
            log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    
    if enable_json_logs:
        console_formatter = JSONFormatter()
    else:
        console_formatter = ColoredConsoleFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handlers (optional)
    if enable_file_logs:
        # General log file (rotates when reaching 10MB)
        general_log_file = log_dir / f"{app_name}.log"
        file_handler = RotatingFileHandler(
            general_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        
        if enable_json_logs:
            file_formatter = JSONFormatter()
        else:
            file_formatter = logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # Error log file (only errors and above, rotates daily)
        error_log_file = log_dir / f"{app_name}_error.log"
        error_handler = TimedRotatingFileHandler(
            error_log_file,
            when='midnight',
            interval=1,
            backupCount=30,  # Keep 30 days of error logs
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)
    
    # Configure third-party loggers to reduce noise
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # Log startup message
    root_logger.info(
        f"Logging initialized - Level: {log_level}, "
        f"JSON: {enable_json_logs}, File logs: {enable_file_logs}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Name of the logger (usually __name__)
    
    Returns:
        Logger instance
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Starting process")
    """
    return logging.getLogger(name)