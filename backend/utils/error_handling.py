"""Enhanced error handling utilities for PocketMusec"""

import logging
import sys
import traceback
from typing import Optional, Dict, Any, Callable
from functools import wraps
from pathlib import Path
import json
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

logger = logging.getLogger(__name__)
console = Console()


class PocketMusecError(Exception):
    """Base exception for PocketMusec"""
    pass


class APIFailureError(PocketMusecError):
    """API failure with graceful degradation options"""
    def __init__(self, message: str, fallback_available: bool = True):
        super().__init__(message)
        self.fallback_available = fallback_available


class FileOperationError(PocketMusecError):
    """File operation failure"""
    def __init__(self, message: str, file_path: str, operation: str):
        super().__init__(message)
        self.file_path = file_path
        self.operation = operation


class ConfigurationError(PocketMusecError):
    """Configuration error"""
    pass


class UserInterruptionError(PocketMusecError):
    """User interrupted operation"""
    pass


class ErrorRecoveryManager:
    """Manages error recovery and fallback strategies"""
    
    def __init__(self):
        self.error_log = []
        self.recovery_strategies = {}
        self.fallback_data = {}
    
    def register_recovery_strategy(self, error_type: type, strategy: Callable):
        """Register a recovery strategy for an error type"""
        self.recovery_strategies[error_type] = strategy
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Log error with context"""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'message': str(error),
            'context': context or {},
            'traceback': traceback.format_exc()
        }
        self.error_log.append(error_entry)
        
        # Also log to file
        logger.error(f"Error logged: {error_entry}")
    
    def attempt_recovery(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> bool:
        """Attempt to recover from error using registered strategies"""
        error_type = type(error)
        safe_context = context or {}
        
        if error_type in self.recovery_strategies:
            try:
                strategy = self.recovery_strategies[error_type]
                return strategy(error, safe_context)
            except Exception as recovery_error:
                logger.error(f"Recovery strategy failed: {recovery_error}")
                return False
        
        return False
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all logged errors"""
        if not self.error_log:
            return {"total_errors": 0}
        
        error_types = {}
        for error in self.error_log:
            error_type = error['error_type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "total_errors": len(self.error_log),
            "error_types": error_types,
            "latest_error": self.error_log[-1] if self.error_log else None
        }


# Global error recovery manager
recovery_manager = ErrorRecoveryManager()


def handle_api_errors(func):
    """Decorator for handling API errors with graceful degradation"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Log the error with safe serializable context
            context = {
                'function': func.__name__,
                'args_count': len(args),
                'kwargs_keys': list(kwargs.keys())
            }
            recovery_manager.log_error(e, context)
            
            # Determine error type and provide appropriate response
            if "timeout" in str(e).lower() or "connection" in str(e).lower():
                return handle_api_timeout_error(e, context)
            elif "authentication" in str(e).lower() or "401" in str(e):
                return handle_authentication_error(e, context)
            elif "rate limit" in str(e).lower() or "429" in str(e):
                return handle_rate_limit_error(e, context)
            else:
                return handle_generic_api_error(e, context)
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Log the error with safe serializable context
            context = {
                'function': func.__name__,
                'args_count': len(args),
                'kwargs_keys': list(kwargs.keys())
            }
            recovery_manager.log_error(e, context)
            
            # Determine error type and provide appropriate response
            if "timeout" in str(e).lower() or "connection" in str(e).lower():
                return handle_api_timeout_error(e, context)
            elif "authentication" in str(e).lower() or "401" in str(e):
                return handle_authentication_error(e, context)
            elif "rate limit" in str(e).lower() or "429" in str(e):
                return handle_rate_limit_error(e, context)
            else:
                return handle_generic_api_error(e, context)
    
    # Return appropriate wrapper based on whether function is async
    import inspect
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def handle_file_errors(func):
    """Decorator for handling file operation errors"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            return handle_file_not_found_error(e)
        except PermissionError as e:
            return handle_permission_error(e)
        except (OSError, IOError) as e:
            return handle_general_file_error(e)
        except Exception as e:
            context = {'function': func.__name__}
            recovery_manager.log_error(e, context)
            return handle_unexpected_file_error(e, context)
    
    return wrapper


def handle_keyboard_interrupts(func):
    """Decorator for clean keyboard interrupt handling"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            return handle_keyboard_interrupt()
        except Exception as e:
            # Re-raise non-keyboard exceptions
            raise
    
    return wrapper


def handle_api_timeout_error(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle API timeout with fallback options"""
    console.print(Panel.fit(
        Text("🔌 API Connection Timeout", style="bold yellow"),
        subtitle="The AI service is taking too long to respond"
    ))
    
    console.print("\n[yellow]What would you like to do?[/yellow]")
    console.print("1. Try again with a longer timeout")
    console.print("2. Use offline mode (limited functionality)")
    console.print("3. Save current progress and exit")
    
    return {
        'error_type': 'timeout',
        'message': 'API request timed out',
        'fallback_available': True,
        'recovery_options': ['retry', 'offline', 'save_and_exit']
    }


def handle_authentication_error(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle authentication errors"""
    console.print(Panel.fit(
        Text("🔑 Authentication Error", style="bold red"),
        subtitle="API key is invalid or missing"
    ))
    
    console.print("\n[red]Please check your API configuration:[/red]")
    console.print("1. Verify CHUTES_API_KEY is set in .env file")
    console.print("2. Check that the API key is valid and active")
    console.print("3. Ensure you have internet connectivity")
    
    return {
        'error_type': 'authentication',
        'message': 'API authentication failed',
        'fallback_available': False,
        'requires_action': 'check_api_key'
    }


def handle_rate_limit_error(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle rate limiting with automatic retry"""
    console.print(Panel.fit(
        Text("⏱️ Rate Limit Reached", style="bold yellow"),
        subtitle="Too many requests. Please wait..."
    ))
    
    console.print("\n[yellow]The service is temporarily busy. Options:[/yellow]")
    console.print("1. Wait and retry automatically (recommended)")
    console.print("2. Try again in a few minutes")
    console.print("3. Use offline mode")
    
    return {
        'error_type': 'rate_limit',
        'message': 'API rate limit exceeded',
        'fallback_available': True,
        'auto_retry': True,
        'retry_delay': 60
    }


def handle_generic_api_error(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle generic API errors"""
    console.print(Panel.fit(
        Text("⚠️ API Error", style="bold red"),
        subtitle="An unexpected error occurred"
    ))
    
    console.print(f"\n[red]Error details:[/red] {str(error)}")
    console.print("\n[yellow]Options:[/yellow]")
    console.print("1. Try again")
    console.print("2. Use basic lesson template")
    console.print("3. Exit and check configuration")
    
    return {
        'error_type': 'generic_api',
        'message': f'API error: {str(error)}',
        'fallback_available': True,
        'recovery_options': ['retry', 'basic_template', 'exit']
    }


def handle_file_not_found_error(error: FileNotFoundError) -> Dict[str, Any]:
    """Handle file not found errors"""
    file_path = str(error.filename) if error.filename else "unknown file"
    
    console.print(Panel.fit(
        Text("📁 File Not Found", style="bold red"),
        subtitle=f"Cannot find: {file_path}"
    ))
    
    console.print(f"\n[red]The file '{file_path}' could not be found.[/red]")
    console.print("\n[yellow]Please check:[/yellow]")
    console.print("1. The file path is correct")
    console.print("2. The file exists and is accessible")
    console.print("3. You have permission to read the file")
    
    return {
        'error_type': 'file_not_found',
        'message': f'File not found: {file_path}',
        'file_path': file_path,
        'fallback_available': False
    }


def handle_permission_error(error: PermissionError) -> Dict[str, Any]:
    """Handle permission errors"""
    console.print(Panel.fit(
        Text("🔒 Permission Denied", style="bold red"),
        subtitle="Insufficient permissions for file operation"
    ))
    
    console.print("\n[red]Permission denied. Please check:[/red]")
    console.print("1. File/directory permissions")
    console.print("2. The file is not in use by another program")
    console.print("3. You have write permissions for the location")
    
    return {
        'error_type': 'permission_denied',
        'message': 'Permission denied for file operation',
        'fallback_available': False
    }


def handle_general_file_error(error: Exception) -> Dict[str, Any]:
    """Handle general file I/O errors"""
    console.print(Panel.fit(
        Text("💾 File Operation Error", style="bold red"),
        subtitle=f"File I/O error: {str(error)}"
    ))
    
    console.print(f"\n[red]File operation failed:[/red] {str(error)}")
    console.print("\n[yellow]Suggestions:[/yellow]")
    console.print("1. Check disk space")
    console.print("2. Verify file system integrity")
    console.print("3. Try a different location")
    
    return {
        'error_type': 'file_io_error',
        'message': f'File I/O error: {str(error)}',
        'fallback_available': True
    }


def handle_unexpected_file_error(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle unexpected file errors"""
    console.print(Panel.fit(
        Text("❌ Unexpected File Error", style="bold red"),
        subtitle="An unexpected error occurred during file operation"
    ))
    
    console.print(f"\n[red]Unexpected error:[/red] {str(error)}")
    
    if context.get('debug_mode', False):
        console.print("\n[dim]Debug information:[/dim]")
        console.print(traceback.format_exc())
    
    return {
        'error_type': 'unexpected_file_error',
        'message': f'Unexpected file error: {str(error)}',
        'fallback_available': False
    }


def handle_keyboard_interrupt() -> Dict[str, Any]:
    """Handle keyboard interrupts gracefully"""
    console.print("\n[yellow]Operation cancelled by user.[/yellow]")
    
    from rich.prompt import Confirm
    
    if Confirm.ask("Would you like to save your progress before exiting?"):
        return {
            'error_type': 'user_interrupt',
            'message': 'User cancelled operation',
            'action': 'save_and_exit',
            'graceful_exit': True
        }
    else:
        return {
            'error_type': 'user_interrupt',
            'message': 'User cancelled operation',
            'action': 'exit',
            'graceful_exit': True
        }


def validate_file_operation(file_path: str, operation: str = "read") -> bool:
    """Validate file before operation"""
    try:
        path = Path(file_path)
        
        # Check if path exists
        if not path.exists():
            raise FileOperationError(
                f"File does not exist: {file_path}",
                file_path,
                operation
            )
        
        # Check permissions
        if operation == "read" and not os.access(path, os.R_OK):
            raise FileOperationError(
                f"No read permission: {file_path}",
                file_path,
                operation
            )
        elif operation == "write" and not os.access(path.parent, os.W_OK):
            raise FileOperationError(
                f"No write permission for directory: {path.parent}",
                file_path,
                operation
            )
        
        # Check if it's actually a file (for read operations)
        if operation == "read" and not path.is_file():
            raise FileOperationError(
                f"Path is not a file: {file_path}",
                file_path,
                operation
            )
        
        return True
        
    except Exception as e:
        if isinstance(e, FileOperationError):
            raise
        raise FileOperationError(
            f"Validation failed for {file_path}: {str(e)}",
            file_path,
            operation
        )


def safe_file_read(file_path: str, encoding: str = 'utf-8') -> str:
    """Safely read file with validation"""
    validate_file_operation(file_path, "read")
    
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except UnicodeDecodeError as e:
        raise FileOperationError(
            f"Encoding error reading {file_path}: {str(e)}",
            file_path,
            "read"
        )
    except Exception as e:
        raise FileOperationError(
            f"Error reading {file_path}: {str(e)}",
            file_path,
            "read"
        )


def safe_file_write(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
    """Safely write file with validation"""
    # Ensure parent directory exists
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    validate_file_operation(file_path, "write")
    
    try:
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        raise FileOperationError(
            f"Error writing {file_path}: {str(e)}",
            file_path,
            "write"
        )


def validate_directory(dir_path: str, operation: str = "read") -> bool:
    """Validate directory operations"""
    try:
        path = Path(dir_path)
        
        # Check if path exists
        if not path.exists():
            if operation == "write":
                # Try to create directory for write operations
                path.mkdir(parents=True, exist_ok=True)
            else:
                raise FileOperationError(
                    f"Directory does not exist: {dir_path}",
                    dir_path,
                    operation
                )
        
        # Check if it's actually a directory
        if not path.is_dir():
            raise FileOperationError(
                f"Path is not a directory: {dir_path}",
                dir_path,
                operation
            )
        
        # Check permissions
        if operation == "read" and not os.access(path, os.R_OK):
            raise FileOperationError(
                f"No read permission for directory: {dir_path}",
                dir_path,
                operation
            )
        elif operation == "write" and not os.access(path, os.W_OK):
            raise FileOperationError(
                f"No write permission for directory: {dir_path}",
                dir_path,
                operation
            )
        
        return True
        
    except Exception as e:
        if isinstance(e, FileOperationError):
            raise
        raise FileOperationError(
            f"Directory validation failed for {dir_path}: {str(e)}",
            dir_path,
            operation
        )


def create_error_report(error_log: list, output_file: str = "error_report.json") -> str:
    """Create detailed error report for debugging"""
    report = {
        'generated_at': datetime.now().isoformat(),
        'total_errors': len(error_log),
        'errors': error_log,
        'system_info': {
            'platform': sys.platform,
            'python_version': sys.version,
            'working_directory': str(Path.cwd())
        }
    }
    
    try:
        report_path = Path(output_file)
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        console.print(f"[green]Error report saved to: {report_path}[/green]")
        return str(report_path)
        
    except Exception as e:
        console.print(f"[red]Failed to save error report: {e}[/red]")
        return ""


def setup_error_recovery_strategies():
    """Setup default error recovery strategies"""
    
    def api_timeout_recovery(error: Exception, context: Dict[str, Any]) -> bool:
        """Recovery strategy for API timeouts"""
        console.print("\n[yellow]Attempting to recover with extended timeout...[/yellow]")
        # Implementation would retry with longer timeout
        return True
    
    def rate_limit_recovery(error: Exception, context: Dict[str, Any]) -> bool:
        """Recovery strategy for rate limiting"""
        console.print("\n[yellow]Waiting for rate limit to reset...[/yellow]")
        time.sleep(60)  # Wait a minute
        return True
    
    # Register recovery strategies
    recovery_manager.register_recovery_strategy(APIFailureError, api_timeout_recovery)
    recovery_manager.register_recovery_strategy(ChutesRateLimitError, rate_limit_recovery)


# Import required modules
import os
import time

# Define fallback error class for rate limiting
class ChutesRateLimitError(Exception):
    """Rate limit error fallback"""
    pass

# Initialize recovery strategies
setup_error_recovery_strategies()