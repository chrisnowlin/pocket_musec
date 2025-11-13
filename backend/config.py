"""Unified configuration management for pocket_musec"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)


@dataclass
class APIConfig:
    """API server configuration"""
    host: str = field(default_factory=lambda: os.getenv("API_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("API_PORT", "8000")))
    reload: bool = field(default_factory=lambda: os.getenv("API_RELOAD", "true").lower() == "true")
    cors_origins: List[str] = field(default_factory=lambda: [
        origin.strip() for origin in os.getenv(
            "CORS_ORIGINS", 
            "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
        ).split(",")
    ])
    docs_url: str = "/api/docs"
    redoc_url: str = "/api/redoc"
    openapi_url: str = "/api/openapi.json"
    version: str = "0.3.0"


@dataclass
class DatabaseConfig:
    """Database configuration"""
    path: str = field(default_factory=lambda: os.getenv("DATABASE_PATH", "data/pocket_musec.db"))
    timeout: int = 30
    check_same_thread: bool = False
    
    def __post_init__(self):
        """Ensure path is absolute and directory exists"""
        if not Path(self.path).is_absolute():
            project_root = Path(__file__).parent.parent.parent
            self.path = str(project_root / self.path)
        
        # Ensure database directory exists
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)


@dataclass
class ChutesConfig:
    """Chutes API configuration"""
    api_key: Optional[str] = field(default_factory=lambda: os.getenv('CHUTES_API_KEY'))
    base_url: str = field(default_factory=lambda: os.getenv('CHUTES_API_BASE_URL', 'https://llm.chutes.ai/v1'))
    embedding_base_url: str = field(default_factory=lambda: os.getenv('CHUTES_EMBEDDING_BASE_URL', 'https://chutes-qwen-qwen3-embedding-8b.chutes.ai/v1'))
    timeout: int = 120
    max_retries: int = 3
    rate_limit_delay: float = 1.0


@dataclass
class LLMConfig:
    """LLM configuration"""
    default_model: str = field(default_factory=lambda: os.getenv('DEFAULT_MODEL', 'Qwen/Qwen3-VL-235B-A22B-Instruct'))
    embedding_model: str = field(default_factory=lambda: os.getenv('EMBEDDING_MODEL', 'Qwen/Qwen3-Embedding-8B'))
    default_temperature: float = field(default_factory=lambda: float(os.getenv('DEFAULT_TEMPERATURE', '0.7')))
    default_max_tokens: int = field(default_factory=lambda: int(os.getenv('DEFAULT_MAX_TOKENS', '2000')))
    streaming_max_tokens: int = 4000
    vision_temperature: float = 0.1
    vision_max_tokens: int = 3000


@dataclass
class OllamaConfig:
    """Ollama local provider configuration"""
    base_url: str = field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen3:8b"))
    timeout: int = 120
    pull_timeout: Optional[int] = None  # No timeout for model downloads


@dataclass
class ImageProcessingConfig:
    """Image processing configuration"""
    storage_path: str = field(default_factory=lambda: os.getenv("IMAGE_STORAGE_PATH", "data/images"))
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_formats: List[str] = field(default_factory=lambda: ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.tiff', '.tif'])
    compression_quality: int = 85
    thumbnail_size: tuple = (800, 600)
    
    def __post_init__(self):
        """Ensure storage directory exists"""
        if not Path(self.storage_path).is_absolute():
            project_root = Path(__file__).parent.parent.parent
            self.storage_path = str(project_root / self.storage_path)
        
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    log_dir: str = "logs"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    error_max_file_size: int = 5 * 1024 * 1024  # 5MB
    error_backup_count: int = 3
    structured_format: bool = True
    console_format: bool = True
    debug_mode: bool = field(default_factory=lambda: os.getenv("DEBUG_MODE", "false").lower() == "true")
    
    def __post_init__(self):
        """Ensure log directory exists"""
        if not Path(self.log_dir).is_absolute():
            project_root = Path(__file__).parent.parent.parent
            self.log_dir = str(project_root / self.log_dir)
        
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)


@dataclass
class WebSearchConfig:
    """Web search service configuration for Brave Search MCP integration"""
    api_key: Optional[str] = field(default_factory=lambda: os.getenv("BRAVE_SEARCH_API_KEY"))
    cache_ttl: int = field(default_factory=lambda: int(os.getenv("WEB_SEARCH_CACHE_TTL", "3600")))  # 1 hour
    max_cache_size: int = field(default_factory=lambda: int(os.getenv("WEB_SEARCH_MAX_CACHE_SIZE", "100")))
    timeout: int = field(default_factory=lambda: int(os.getenv("WEB_SEARCH_TIMEOUT", "30")))  # 30 seconds
    educational_only: bool = field(default_factory=lambda: os.getenv("WEB_SEARCH_EDUCATIONAL_ONLY", "false").lower() == "true")
    min_relevance_score: float = field(default_factory=lambda: float(os.getenv("WEB_SEARCH_MIN_RELEVANCE_SCORE", "0.3")))
    max_results: int = field(default_factory=lambda: int(os.getenv("WEB_SEARCH_MAX_RESULTS", "10")))


@dataclass
class FileStorageConfig:
    """File storage configuration"""
    storage_root: str = field(default_factory=lambda: os.getenv("FILE_STORAGE_ROOT", "data/uploads"))
    max_file_size: int = field(default_factory=lambda: int(os.getenv("MAX_FILE_SIZE", str(50 * 1024 * 1024))))  # 50MB
    allowed_extensions: List[str] = field(default_factory=lambda: [
        ext.strip() for ext in os.getenv("ALLOWED_EXTENSIONS", ".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif,.webp,.tiff,.tif").split(",")
    ])
    duplicate_detection: bool = field(default_factory=lambda: os.getenv("DUPLICATE_DETECTION", "true").lower() == "true")
    retention_days: int = field(default_factory=lambda: int(os.getenv("FILE_RETENTION_DAYS", "365")))
    cleanup_enabled: bool = field(default_factory=lambda: os.getenv("FILE_CLEANUP_ENABLED", "true").lower() == "true")
    
    def __post_init__(self):
        """Ensure storage directory exists"""
        if not Path(self.storage_root).is_absolute():
            project_root = Path(__file__).parent.parent.parent
            self.storage_root = str(project_root / self.storage_root)
        
        Path(self.storage_root).mkdir(parents=True, exist_ok=True)


@dataclass
class ProcessingConfig:
    """Processing and performance configuration"""
    batch_size: int = 10
    parallel_workers: int = 4
    request_timeout: int = 120
    max_retries: int = 3
    retry_delay: float = 1.0
    cache_ttl: int = 3600  # 1 hour
    max_cache_size: int = 1000


@dataclass
class SecurityConfig:
    """Security configuration"""
    demo_mode: bool = True  # Single-user demo mode without authentication
    jwt_secret_key: Optional[str] = field(default_factory=lambda: os.getenv('JWT_SECRET_KEY'))
    rate_limit_per_minute: int = 60
    max_request_size: int = 16 * 1024 * 1024  # 16MB
    
    def __post_init__(self):
        """Set demo mode based on JWT secret availability"""
        self.demo_mode = not bool(self.jwt_secret_key)


@dataclass
class PathConfig:
    """Path configuration"""
    data_root: str = "data"
    standards_dir: str = "data/standards"
    prepared_texts_dir: str = "data/prepared_texts"
    uploads_dir: str = "data/uploads"
    temp_dir: str = "data/temp"
    
    def __post_init__(self):
        """Ensure all paths are absolute and directories exist"""
        project_root = Path(__file__).parent.parent.parent
        
        path_mappings = {
            'data_root': self.data_root,
            'standards_dir': self.standards_dir,
            'prepared_texts_dir': self.prepared_texts_dir,
            'uploads_dir': self.uploads_dir,
            'temp_dir': self.temp_dir
        }
        
        for attr_name, path_value in path_mappings.items():
            if not Path(path_value).is_absolute():
                setattr(self, attr_name, str(project_root / path_value))
            
            # Create directory if it doesn't exist
            Path(getattr(self, attr_name)).mkdir(parents=True, exist_ok=True)


class Config:
    """Unified application configuration"""
    
    def __init__(self):
        """Initialize all configuration sections"""
        self.api = APIConfig()
        self.database = DatabaseConfig()
        self.chutes = ChutesConfig()
        self.llm = LLMConfig()
        self.ollama = OllamaConfig()
        self.image_processing = ImageProcessingConfig()
        self.logging = LoggingConfig()
        self.processing = ProcessingConfig()
        self.security = SecurityConfig()
        self.paths = PathConfig()
        self.file_storage = FileStorageConfig()
        self.web_search = WebSearchConfig()
        
        # Validate configuration
        self.validate()
    
    def validate(self) -> None:
        """Validate required configuration"""
        # Validate Chutes API key if needed
        if self.is_cloud_enabled() and not self.chutes.api_key:
            raise ValueError(
                "CHUTES_API_KEY not found. Please set it in .env file or environment variables."
            )
        
        # Validate essential directories
        essential_dirs = [
            self.paths.data_root,
            self.paths.standards_dir,
            self.logging.log_dir
        ]
        
        for dir_path in essential_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def is_cloud_enabled(self) -> bool:
        """Check if cloud processing is enabled"""
        return bool(self.chutes.api_key)
    
    def is_local_enabled(self) -> bool:
        """Check if local processing is available"""
        return True  # Always available if Ollama is installed
    
    def get_database_url(self) -> str:
        """Get database connection URL"""
        return f"sqlite:///{self.database.path}"
    
    def get_log_config(self) -> Dict[str, Any]:
        """Get logging configuration dictionary"""
        return {
            'level': self.logging.level,
            'log_dir': self.logging.log_dir,
            'max_file_size': self.logging.max_file_size,
            'backup_count': self.logging.backup_count,
            'structured_format': self.logging.structured_format,
            'console_format': self.logging.console_format,
            'debug_mode': self.logging.debug_mode
        }
    
    def get_cors_config(self) -> Dict[str, Any]:
        """Get CORS configuration dictionary"""
        return {
            'allow_origins': self.api.cors_origins,
            'allow_credentials': True,
            'allow_methods': ["*"],
            'allow_headers': ["*"]
        }
    
    def is_configured(self) -> bool:
        """Check if minimum required configuration is present"""
        # In demo mode, we just need basic functionality
        return True
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get environment information for debugging"""
        return {
            'demo_mode': self.security.demo_mode,
            'cloud_enabled': self.is_cloud_enabled(),
            'local_enabled': self.is_local_enabled(),
            'database_path': self.database.path,
            'data_root': self.paths.data_root,
            'log_level': self.logging.level,
            'api_version': self.api.version
        }
    


# Create global config instance
config = Config()


# Convenience functions for backward compatibility
def get_config() -> Config:
    """Get global configuration instance"""
    return config


def validate_config() -> None:
    """Validate configuration"""
    config.validate()


def is_configured() -> bool:
    """Check if configuration is valid"""
    return config.is_configured()


# Environment-specific configurations
class EnvironmentConfig:
    """Environment-specific configuration management"""
    
    @staticmethod
    def is_development() -> bool:
        """Check if running in development mode"""
        return os.getenv("ENVIRONMENT", "development").lower() == "development"
    
    @staticmethod
    def is_production() -> bool:
        """Check if running in production mode"""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    @staticmethod
    def is_testing() -> bool:
        """Check if running in testing mode"""
        return os.getenv("ENVIRONMENT", "development").lower() == "testing"
    
    @staticmethod
    def get_environment() -> str:
        """Get current environment"""
        return os.getenv("ENVIRONMENT", "development")


# Export commonly used configuration values for backward compatibility
CHUTES_API_KEY = config.chutes.api_key
CHUTES_API_BASE_URL = config.chutes.base_url
CHUTES_EMBEDDING_BASE_URL = config.chutes.embedding_base_url
DEFAULT_MODEL = config.llm.default_model
EMBEDDING_MODEL = config.llm.embedding_model
DEFAULT_TEMPERATURE = config.llm.default_temperature
DEFAULT_MAX_TOKENS = config.llm.default_max_tokens
DATABASE_PATH = config.database.path
API_HOST = config.api.host
API_PORT = config.api.port
API_RELOAD = config.api.reload
CORS_ORIGINS = config.api.cors_origins
OLLAMA_BASE_URL = config.ollama.base_url
OLLAMA_MODEL = config.ollama.model
IMAGE_STORAGE_PATH = config.image_processing.storage_path
FILE_STORAGE_ROOT = config.file_storage.storage_root
MAX_FILE_SIZE = config.file_storage.max_file_size
ALLOWED_EXTENSIONS = config.file_storage.allowed_extensions
DUPLICATE_DETECTION = config.file_storage.duplicate_detection
FILE_RETENTION_DAYS = config.file_storage.retention_days
FILE_CLEANUP_ENABLED = config.file_storage.cleanup_enabled
BRAVE_SEARCH_API_KEY = config.web_search.api_key
WEB_SEARCH_CACHE_TTL = config.web_search.cache_ttl
WEB_SEARCH_MAX_CACHE_SIZE = config.web_search.max_cache_size
WEB_SEARCH_TIMEOUT = config.web_search.timeout
WEB_SEARCH_EDUCATIONAL_ONLY = config.web_search.educational_only
WEB_SEARCH_MIN_RELEVANCE_SCORE = config.web_search.min_relevance_score
WEB_SEARCH_MAX_RESULTS = config.web_search.max_results
