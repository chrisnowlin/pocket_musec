"""Comprehensive logging configuration for PocketMusec"""

import logging
import logging.handlers
import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from contextlib import contextmanager

from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text


@dataclass
class LogEntry:
    """Structured log entry for consistent formatting"""
    timestamp: str
    level: str
    message: str
    module: str
    function: str
    line_number: int
    context: Optional[Dict[str, Any]] = None
    error_details: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = LogEntry(
            timestamp=datetime.fromtimestamp(record.created).isoformat(),
            level=record.levelname,
            message=record.getMessage(),
            module=record.module,
            function=record.funcName,
            line_number=record.lineno,
            context=getattr(record, 'context', None),
            error_details=getattr(record, 'error_details', None),
            user_id=getattr(record, 'user_id', None),
            session_id=getattr(record, 'session_id', None)
        )
        
        return json.dumps(asdict(log_entry), default=str)


class ColoredConsoleFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    COLORS = {
        'DEBUG': 'dim cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold red'
    }
    
    def format(self, record: logging.LogRecord) -> str:
        # Add color based on level
        level_color = self.COLORS.get(record.levelname, 'white')
        level_text = f"[{level_color}]{record.levelname}[/{level_color}]"
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        
        # Build message
        message = record.getMessage()
        if hasattr(record, 'context') and getattr(record, 'context', None):
            context_str = f" | Context: {getattr(record, 'context')}"
            message += context_str
        
        if hasattr(record, 'error_details') and getattr(record, 'error_details', None):
            error_str = f" | Error: {getattr(record, 'error_details')}"
            message += error_str
        
        return f"[dim]{timestamp}[/dim] {level_text} [cyan]{record.name}[/cyan] {message}"


class PocketMusecLogger:
    """Enhanced logger with structured logging and file rotation"""
    
    def __init__(self, name: str = "pocketmusec"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.console = Console()
        self.session_id = self._generate_session_id()
        self._setup_logger()
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _setup_logger(self):
        """Setup logger with handlers"""
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set log level
        self.logger.setLevel(logging.DEBUG)
        
        # Console handler with Rich formatting
        console_handler = RichHandler(
            console=self.console,
            show_time=True,
            show_path=True,
            markup=True,
            rich_tracebacks=True
        )
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredConsoleFormatter()
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for structured logs
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / f"{self.name}.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = StructuredFormatter()
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / f"{self.name}_errors.log",
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        self.logger.addHandler(error_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error message with optional exception details"""
        if error:
            kwargs['error_details'] = {
                'type': type(error).__name__,
                'message': str(error),
                'traceback': self._get_traceback(error)
            }
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log critical message"""
        if error:
            kwargs['error_details'] = {
                'type': type(error).__name__,
                'message': str(error),
                'traceback': self._get_traceback(error)
            }
        self._log(logging.CRITICAL, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method"""
        # Add session ID to all logs
        kwargs['session_id'] = self.session_id
        
        # Create log record with extra data
        extra = {}
        if kwargs.get('context'):
            extra['context'] = kwargs.get('context')
        if kwargs.get('error_details'):
            extra['error_details'] = kwargs.get('error_details')
        if kwargs.get('user_id'):
            extra['user_id'] = kwargs.get('user_id')
        if kwargs.get('session_id'):
            extra['session_id'] = kwargs.get('session_id')
        
        self.logger.log(level, message, extra=extra)
    
    def _get_traceback(self, error: Exception) -> str:
        """Get formatted traceback for exception"""
        import traceback
        return traceback.format_exc()
    
    def log_api_call(self, endpoint: str, method: str, status: int, 
                    response_time: float, **kwargs):
        """Log API call with performance metrics"""
        context = {
            'api_endpoint': endpoint,
            'method': method,
            'status_code': status,
            'response_time_ms': round(response_time * 1000, 2),
            **kwargs
        }
        
        if status >= 400:
            self.error(f"API call failed: {method} {endpoint}", context=context)
        else:
            self.info(f"API call: {method} {endpoint}", context=context)
    
    def log_file_operation(self, file_path: str, operation: str, 
                          success: bool, file_size: Optional[int] = None, **kwargs):
        """Log file operations"""
        context = {
            'file_path': file_path,
            'operation': operation,
            'success': success,
            'file_size_bytes': file_size,
            **kwargs
        }
        
        if success:
            self.info(f"File operation: {operation} {file_path}", context=context)
        else:
            self.error(f"File operation failed: {operation} {file_path}", context=context)
    
    def log_lesson_generation(self, lesson_id: str, standards_count: int, 
                             generation_time: float, success: bool, **kwargs):
        """Log lesson generation metrics"""
        context = {
            'lesson_id': lesson_id,
            'standards_count': standards_count,
            'generation_time_seconds': round(generation_time, 2),
            'success': success,
            **kwargs
        }
        
        if success:
            self.info(f"Lesson generated: {lesson_id}", context=context)
        else:
            self.error(f"Lesson generation failed: {lesson_id}", context=context)
    
    def log_user_action(self, action: str, user_id: Optional[str] = None, **kwargs):
        """Log user actions"""
        context = {
            'action': action,
            **kwargs
        }
        
        if user_id:
            context['user_id'] = user_id
        
        self.info(f"User action: {action}", context=context)
    
    @contextmanager
    def log_performance(self, operation: str, **kwargs):
        """Context manager for performance logging"""
        start_time = datetime.now()
        self.debug(f"Starting operation: {operation}", context=kwargs)
        
        try:
            yield
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            context = {
                'operation': operation,
                'duration_seconds': round(duration, 2),
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                **kwargs
            }
            
            self.info(f"Completed operation: {operation}", context=context)
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            context = {
                'operation': operation,
                'duration_seconds': round(duration, 2),
                'failed': True,
                **kwargs
            }
            
            self.error(f"Failed operation: {operation}", error=e, context=context)
            raise
    
    def set_debug_mode(self, enabled: bool = True):
        """Enable or disable debug mode"""
        if enabled:
            self.logger.setLevel(logging.DEBUG)
            for handler in self.logger.handlers:
                if isinstance(handler, RichHandler):
                    handler.setLevel(logging.DEBUG)
            self.info("Debug mode enabled")
        else:
            self.logger.setLevel(logging.INFO)
            for handler in self.logger.handlers:
                if isinstance(handler, RichHandler):
                    handler.setLevel(logging.INFO)
            self.info("Debug mode disabled")
    
    def get_log_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of recent log entries"""
        log_file = Path("logs") / f"{self.name}.log"
        
        if not log_file.exists():
            return {"error": "No log file found"}
        
        try:
            cutoff_time = datetime.now().timestamp() - (hours * 3600)
            
            entry_counts = {'DEBUG': 0, 'INFO': 0, 'WARNING': 0, 'ERROR': 0, 'CRITICAL': 0}
            recent_errors = []
            
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_time = datetime.fromisoformat(entry['timestamp']).timestamp()
                        
                        if entry_time >= cutoff_time:
                            level = entry['level']
                            if level in entry_counts:
                                entry_counts[level] += 1
                            
                            if level in ['ERROR', 'CRITICAL']:
                                recent_errors.append({
                                    'timestamp': entry['timestamp'],
                                    'message': entry['message'],
                                    'module': entry['module']
                                })
                    
                    except (json.JSONDecodeError, KeyError):
                        continue
            
            return {
                'timeframe_hours': hours,
                'entry_counts': entry_counts,
                'total_entries': sum(entry_counts.values()),
                'recent_errors': recent_errors[-10:],  # Last 10 errors
                'session_id': self.session_id
            }
            
        except Exception as e:
            return {"error": f"Failed to read log file: {str(e)}"}
    
    def cleanup_old_logs(self, days: int = 30):
        """Clean up old log files"""
        log_dir = Path("logs")
        if not log_dir.exists():
            return
        
        cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
        cleaned_files = []
        
        for log_file in log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    cleaned_files.append(str(log_file))
                except Exception as e:
                    self.warning(f"Failed to delete old log file {log_file}: {e}")
        
        if cleaned_files:
            self.info(f"Cleaned up {len(cleaned_files)} old log files", 
                     context={'deleted_files': cleaned_files})


# Global logger instance
pocket_logger = PocketMusecLogger()


def get_logger(name: Optional[str] = None) -> PocketMusecLogger:
    """Get logger instance"""
    if name:
        return PocketMusecLogger(name)
    return pocket_logger


def setup_logging(debug: bool = False, log_file: Optional[str] = None):
    """Setup logging configuration"""
    if debug:
        pocket_logger.set_debug_mode(True)
    
    if log_file:
        # Add additional file handler if specified
        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setLevel(logging.DEBUG)
        formatter = StructuredFormatter()
        handler.setFormatter(formatter)
        pocket_logger.logger.addHandler(handler)


# Convenience functions
def log_debug(message: str, **kwargs):
    """Log debug message"""
    pocket_logger.debug(message, **kwargs)


def log_info(message: str, **kwargs):
    """Log info message"""
    pocket_logger.info(message, **kwargs)


def log_warning(message: str, **kwargs):
    """Log warning message"""
    pocket_logger.warning(message, **kwargs)


def log_error(message: str, error: Optional[Exception] = None, **kwargs):
    """Log error message"""
    pocket_logger.error(message, error, **kwargs)


def log_critical(message: str, error: Optional[Exception] = None, **kwargs):
    """Log critical message"""
    pocket_logger.critical(message, error, **kwargs)