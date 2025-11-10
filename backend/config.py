"""Configuration management for pocket_musec"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Application configuration"""
    
    # Chutes API Configuration
    CHUTES_API_KEY: Optional[str] = os.getenv('CHUTES_API_KEY')
    CHUTES_API_BASE_URL: str = os.getenv('CHUTES_API_BASE_URL', 'https://llm.chutes.ai/v1')
    CHUTES_EMBEDDING_BASE_URL: str = os.getenv('CHUTES_EMBEDDING_BASE_URL', 'https://chutes-qwen-qwen3-embedding-8b.chutes.ai/v1')
    
    # LLM Configuration
    DEFAULT_MODEL: str = os.getenv('DEFAULT_MODEL', 'Qwen/Qwen3-VL-235B-A22B-Instruct')
    EMBEDDING_MODEL: str = os.getenv('EMBEDDING_MODEL', 'Qwen/Qwen3-Embedding-8B')
    DEFAULT_TEMPERATURE: float = float(os.getenv('DEFAULT_TEMPERATURE', '0.7'))
    DEFAULT_MAX_TOKENS: int = int(os.getenv('DEFAULT_MAX_TOKENS', '2000'))
    
    # Database Configuration
    DATABASE_PATH: Optional[str] = os.getenv('DATABASE_PATH')
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration"""
        if not cls.CHUTES_API_KEY:
            raise ValueError(
                "CHUTES_API_KEY not found. Please set it in .env file or environment variables."
            )
    
    @classmethod
    def is_configured(cls) -> bool:
        """Check if minimum required configuration is present"""
        return cls.CHUTES_API_KEY is not None


# Create global config instance
config = Config()
