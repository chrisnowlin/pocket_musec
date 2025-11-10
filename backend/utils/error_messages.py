"""Enhanced error messages for better user experience"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.columns import Columns
from rich.align import Align

console = Console()


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better organization"""
    API = "api"
    FILE = "file"
    DATABASE = "database"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    USER_INPUT = "user_input"
    SYSTEM = "system"


@dataclass
class ErrorInfo:
    """Structured error information"""
    title: str
    description: str
    category: ErrorCategory
    severity: ErrorSeverity
    causes: List[str]
    solutions: List[str]
    prevention: Optional[str] = None
    technical_details: Optional[str] = None


class ErrorMessageFormatter:
    """Formats and displays user-friendly error messages"""
    
    def __init__(self):
        self.error_templates = self._load_error_templates()
    
    def _load_error_templates(self) -> Dict[str, ErrorInfo]:
        """Load predefined error message templates"""
        return {
            "api_timeout": ErrorInfo(
                title="🔌 API Connection Timeout",
                description="The AI service is taking too long to respond.",
                category=ErrorCategory.API,
                severity=ErrorSeverity.MEDIUM,
                causes=[
                    "Slow internet connection",
                    "API service is temporarily busy",
                    "Large request processing time",
                    "Network connectivity issues"
                ],
                solutions=[
                    "Check your internet connection",
                    "Try again with a shorter request",
                    "Wait a few minutes and retry",
                    "Use offline mode if available"
                ],
                prevention="Ensure stable internet connection before starting lesson generation.",
                technical_details="Request timed out after 120 seconds"
            ),
            
            "api_auth": ErrorInfo(
                title="🔑 Authentication Error",
                description="API key is invalid, missing, or expired.",
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.HIGH,
                causes=[
                    "API key not set in environment",
                    "Invalid API key format",
                    "API key has expired",
                    "API key permissions insufficient"
                ],
                solutions=[
                    "Set CHUTES_API_KEY in .env file",
                    "Verify API key is correct and active",
                    "Check API key hasn't expired",
                    "Ensure API key has required permissions"
                ],
                prevention="Store API key securely in .env file and keep it updated.",
                technical_details="HTTP 401 Unauthorized response from API"
            ),
            
            "api_rate_limit": ErrorInfo(
                title="⏱️ Rate Limit Reached",
                description="Too many requests sent to the API service.",
                category=ErrorCategory.API,
                severity=ErrorSeverity.MEDIUM,
                causes=[
                    "Too many requests in short time",
                    "Concurrent requests from multiple sessions",
                    "API service under heavy load"
                ],
                solutions=[
                    "Wait a few minutes before retrying",
                    "Reduce request frequency",
                    "Use batch processing when possible",
                    "Upgrade API plan if needed"
                ],
                prevention="Space out requests and avoid unnecessary API calls.",
                technical_details="HTTP 429 Too Many Requests"
            ),
            
            "file_not_found": ErrorInfo(
                title="📁 File Not Found",
                description="The specified file could not be located.",
                category=ErrorCategory.FILE,
                severity=ErrorSeverity.HIGH,
                causes=[
                    "Incorrect file path",
                    "File has been moved or deleted",
                    "File name misspelled",
                    "Wrong directory specified"
                ],
                solutions=[
                    "Verify the file path is correct",
                    "Check if file exists in the specified location",
                    "Use absolute paths instead of relative",
                    "Check file name spelling and case"
                ],
                prevention="Use file browser to verify paths before entering them.",
                technical_details="FileNotFoundError: No such file or directory"
            ),
            
            "file_permission": ErrorInfo(
                title="🔒 Permission Denied",
                description="Insufficient permissions to access the file or directory.",
                category=ErrorCategory.FILE,
                severity=ErrorSeverity.HIGH,
                causes=[
                    "File is in use by another program",
                    "Insufficient user permissions",
                    "Directory is write-protected",
                    "File is system-protected"
                ],
                solutions=[
                    "Close any programs using the file",
                    "Run with administrator privileges if needed",
                    "Check file and directory permissions",
                    "Choose a different save location"
                ],
                prevention="Ensure you have appropriate permissions for the target directory.",
                technical_details="PermissionError: Permission denied"
            ),
            
            "database_error": ErrorInfo(
                title="💾 Database Error",
                description="An error occurred while accessing the database.",
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.HIGH,
                causes=[
                    "Database file is corrupted",
                    "Insufficient disk space",
                    "Database is locked by another process",
                    "Invalid database schema"
                ],
                solutions=[
                    "Restart the application to release database locks",
                    "Check available disk space",
                    "Reinitialize the database if corrupted",
                    "Ensure no other instances are running"
                ],
                prevention="Regularly backup database and avoid force-closing the application.",
                technical_details="SQLite database operation failed"
            ),
            
            "network_error": ErrorInfo(
                title="🌐 Network Connection Error",
                description="Unable to connect to the internet or API service.",
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                causes=[
                    "No internet connection",
                    "DNS resolution failure",
                    "Firewall blocking connection",
                    "API service is down"
                ],
                solutions=[
                    "Check internet connection",
                    "Try different network (WiFi/cellular)",
                    "Disable VPN or proxy temporarily",
                    "Check if API service is operational"
                ],
                prevention="Ensure stable internet connection before using online features.",
                technical_details="Network request failed"
            ),
            
            "invalid_input": ErrorInfo(
                title="❌ Invalid Input",
                description="The provided input is not valid or expected.",
                category=ErrorCategory.USER_INPUT,
                severity=ErrorSeverity.LOW,
                causes=[
                    "Invalid option selected",
                    "Incorrect format for input",
                    "Required field is empty",
                    "Input contains invalid characters"
                ],
                solutions=[
                    "Check the available options and try again",
                    "Follow the specified input format",
                    "Ensure all required fields are filled",
                    "Use only valid characters as specified"
                ],
                prevention="Read instructions carefully and follow the specified format.",
                technical_details="Input validation failed"
            ),
            
            "system_error": ErrorInfo(
                title="⚠️ System Error",
                description="An unexpected system error occurred.",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                causes=[
                    "Insufficient memory",
                    "Operating system error",
                    "Python environment issue",
                    "Missing system dependencies"
                ],
                solutions=[
                    "Restart the application",
                    "Check available system memory",
                    "Update Python and dependencies",
                    "Try running on a different machine"
                ],
                prevention="Keep system updated and ensure sufficient resources are available.",
                technical_details="System-level error occurred"
            )
        }
    
    def format_error(self, error_key: str, context: Dict[str, Any] = None) -> Panel:
        """Format and display an error message"""
        if error_key not in self.error_templates:
            return self._format_generic_error(error_key, context)
        
        error_info = self.error_templates[error_key]
        
        # Create main error panel
        title_text = Text(error_info.title, style=f"bold {self._get_severity_color(error_info.severity)}")
        
        # Build content sections
        content_parts = []
        
        # Description
        content_parts.append(Text(error_info.description, style="white"))
        content_parts.append(Text(""))
        
        # Causes section
        if error_info.causes:
            causes_text = Text("Possible causes:", style="bold yellow")
            content_parts.append(causes_text)
            for cause in error_info.causes:
                content_parts.append(Text(f"• {cause}", style="yellow"))
            content_parts.append(Text(""))
        
        # Solutions section
        if error_info.solutions:
            solutions_text = Text("What you can do:", style="bold green")
            content_parts.append(solutions_text)
            for i, solution in enumerate(error_info.solutions, 1):
                content_parts.append(Text(f"{i}. {solution}", style="green"))
            content_parts.append(Text(""))
        
        # Prevention tip
        if error_info.prevention:
            prevention_text = Text("💡 Tip: ", style="bold cyan") + Text(error_info.prevention, style="cyan")
            content_parts.append(prevention_text)
        
        # Technical details (if in debug mode)
        if context and context.get("debug_mode", False) and error_info.technical_details:
            content_parts.append(Text(""))
            tech_text = Text("Technical details: ", style="dim") + Text(error_info.technical_details, style="dim")
            content_parts.append(tech_text)
        
        # Combine all content
        content = Text("\n").join(content_parts)
        
        return Panel(
            content,
            title=title_text,
            border_style=self._get_severity_color(error_info.severity),
            padding=(1, 2)
        )
    
    def _format_generic_error(self, error_key: str, context: Dict[str, Any] = None) -> Panel:
        """Format a generic error for unknown error types"""
        title = Text("❓ Unknown Error", style="bold red")
        content = Text(f"An unexpected error occurred: {error_key}", style="white")
        
        if context and context.get("debug_mode", False):
            content += Text("\n\nDebug information:", style="dim")
            for key, value in context.items():
                content += Text(f"\n{key}: {value}", style="dim")
        
        return Panel(
            content,
            title=title,
            border_style="red",
            padding=(1, 2)
        )
    
    def _get_severity_color(self, severity: ErrorSeverity) -> str:
        """Get color based on error severity"""
        color_map = {
            ErrorSeverity.LOW: "yellow",
            ErrorSeverity.MEDIUM: "orange3",
            ErrorSeverity.HIGH: "red",
            ErrorSeverity.CRITICAL: "bright_red"
        }
        return color_map.get(severity, "red")
    
    def display_error(self, error_key: str, context: Dict[str, Any] = None):
        """Display formatted error to console"""
        panel = self.format_error(error_key, context)
        console.print("\n")
        console.print(panel)
        console.print("\n")
    
    def display_error_with_recovery(self, error_key: str, recovery_options: List[str], context: Dict[str, Any] = None):
        """Display error with recovery options"""
        self.display_error(error_key, context)
        
        if recovery_options:
            console.print("[bold cyan]Recovery Options:[/bold cyan]")
            for i, option in enumerate(recovery_options, 1):
                console.print(f"{i}. {option}")
            console.print("")


class UserFriendlyErrors:
    """High-level interface for user-friendly error messages"""
    
    def __init__(self):
        self.formatter = ErrorMessageFormatter()
    
    def api_timeout(self, context: Dict[str, Any] = None):
        """Display API timeout error"""
        recovery_options = [
            "Try again with longer timeout",
            "Check internet connection",
            "Use offline mode (limited functionality)",
            "Save progress and exit"
        ]
        self.formatter.display_error_with_recovery("api_timeout", recovery_options, context)
    
    def api_authentication(self, context: Dict[str, Any] = None):
        """Display API authentication error"""
        recovery_options = [
            "Check API key in .env file",
            "Verify API key is valid",
            "Update API key if expired",
            "Contact support for help"
        ]
        self.formatter.display_error_with_recovery("api_auth", recovery_options, context)
    
    def api_rate_limit(self, context: Dict[str, Any] = None):
        """Display rate limit error"""
        recovery_options = [
            "Wait and retry automatically",
            "Try again in a few minutes",
            "Use offline mode",
            "Upgrade API plan"
        ]
        self.formatter.display_error_with_recovery("api_rate_limit", recovery_options, context)
    
    def file_not_found(self, file_path: str, context: Dict[str, Any] = None):
        """Display file not found error"""
        error_context = {"file_path": file_path}
        if context:
            error_context.update(context)
        
        recovery_options = [
            "Check file path and name",
            "Browse to locate file",
            "Use absolute path",
            "Try different file"
        ]
        self.formatter.display_error_with_recovery("file_not_found", recovery_options, error_context)
    
    def file_permission(self, file_path: str, context: Dict[str, Any] = None):
        """Display file permission error"""
        error_context = {"file_path": file_path}
        if context:
            error_context.update(context)
        
        recovery_options = [
            "Close file in other programs",
            "Choose different save location",
            "Run as administrator",
            "Check file permissions"
        ]
        self.formatter.display_error_with_recovery("file_permission", recovery_options, error_context)
    
    def database_error(self, operation: str, context: Dict[str, Any] = None):
        """Display database error"""
        error_context = {"operation": operation}
        if context:
            error_context.update(context)
        
        recovery_options = [
            "Restart application",
            "Check disk space",
            "Reinitialize database",
            "Contact support"
        ]
        self.formatter.display_error_with_recovery("database_error", recovery_options, error_context)
    
    def network_error(self, context: Dict[str, Any] = None):
        """Display network error"""
        recovery_options = [
            "Check internet connection",
            "Try different network",
            "Disable VPN/proxy",
            "Use offline mode"
        ]
        self.formatter.display_error_with_recovery("network_error", recovery_options, context)
    
    def invalid_input(self, input_value: str, expected: str, context: Dict[str, Any] = None):
        """Display invalid input error"""
        error_context = {"input": input_value, "expected": expected}
        if context:
            error_context.update(context)
        
        recovery_options = [
            "Check available options",
            "Follow specified format",
            "Try again with correct input",
            "Use help for guidance"
        ]
        self.formatter.display_error_with_recovery("invalid_input", recovery_options, error_context)
    
    def system_error(self, error_details: str, context: Dict[str, Any] = None):
        """Display system error"""
        error_context = {"details": error_details}
        if context:
            error_context.update(context)
        
        recovery_options = [
            "Restart application",
            "Check system resources",
            "Update dependencies",
            "Contact technical support"
        ]
        self.formatter.display_error_with_recovery("system_error", recovery_options, error_context)
    
    def generic_error(self, error_message: str, context: Dict[str, Any] = None):
        """Display generic error"""
        error_context = {"message": error_message}
        if context:
            error_context.update(context)
        
        recovery_options = [
            "Try the operation again",
            "Check input and try different approach",
            "Restart application",
            "Contact support if problem persists"
        ]
        self.formatter.display_error_with_recovery("generic_error", recovery_options, error_context)


# Global instance for easy access
user_errors = UserFriendlyErrors()


# Convenience functions for common error scenarios
def show_api_error(error_type: str, context: Dict[str, Any] = None):
    """Show API-related error"""
    if error_type == "timeout":
        user_errors.api_timeout(context)
    elif error_type == "auth":
        user_errors.api_authentication(context)
    elif error_type == "rate_limit":
        user_errors.api_rate_limit(context)
    else:
        user_errors.generic_error(f"API error: {error_type}", context)


def show_file_error(error_type: str, file_path: str, context: Dict[str, Any] = None):
    """Show file-related error"""
    if error_type == "not_found":
        user_errors.file_not_found(file_path, context)
    elif error_type == "permission":
        user_errors.file_permission(file_path, context)
    else:
        user_errors.generic_error(f"File error: {error_type}", context)


def show_system_error(error_type: str, details: str, context: Dict[str, Any] = None):
    """Show system-related error"""
    if error_type == "database":
        user_errors.database_error(details, context)
    elif error_type == "network":
        user_errors.network_error(context)
    elif error_type == "system":
        user_errors.system_error(details, context)
    else:
        user_errors.generic_error(f"System error: {error_type}", context)