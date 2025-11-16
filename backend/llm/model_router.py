"""Model router for switching between cloud and local LLM providers"""

from typing import Optional, Literal, List, Dict, Any
from enum import Enum
import logging

from .chutes_client import ChutesClient, Message
from .local_provider import OllamaProvider
from backend.config import config

logger = logging.getLogger(__name__)


class ProcessingMode(str, Enum):
    """Processing mode enumeration"""

    CLOUD = "cloud"
    LOCAL = "local"


class ModelRouter:
    """
    Routes generation requests to appropriate LLM provider

    Switches between cloud (Chutes) and local (Ollama) based on user preference
    """

    # Available Chutes API models
    AVAILABLE_CLOUD_MODELS = [
        {
            "id": "moonshotai/Kimi-K2-Thinking",
            "name": "Kimi K2 Thinking (Default)",
            "description": "Advanced reasoning model with step-by-step thinking - produces comprehensive, detailed lesson plans with enhanced pedagogical depth",
            "capabilities": ["text", "reasoning", "detailed-planning"],
            "recommended": True,
        },
        {
            "id": "Qwen/Qwen3-VL-235B-A22B-Instruct",
            "name": "Qwen3-VL",
            "description": "High-quality multimodal model with vision capabilities - faster for quick lesson outlines",
            "capabilities": ["text", "vision"],
            "recommended": False,
        },
    ]

    def __init__(self):
        # Initialize providers
        self.cloud_provider = None
        self.local_provider = None

        # Initialize cloud provider if API key available
        if config.is_cloud_enabled():
            try:
                self.cloud_provider = ChutesClient(api_key=config.chutes.api_key)
                logger.info("Cloud provider (Chutes) initialized")
            except Exception as e:
                logger.error(f"Failed to initialize cloud provider: {e}")

        # Initialize local provider
        try:
            self.local_provider = OllamaProvider(
                base_url=config.ollama.base_url,
                model=config.ollama.model,
                timeout=config.ollama.timeout,
            )
            logger.info("Local provider (Ollama) initialized")
        except Exception as e:
            logger.error(f"Failed to initialize local provider: {e}")

    def generate(
        self,
        prompt: str,
        mode: ProcessingMode,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        model: Optional[str] = None,
    ) -> str:
        """
        Generate text using specified mode

        Args:
            prompt: User prompt
            mode: Processing mode (cloud or local)
            system_prompt: Optional system prompt
            temperature: Temperature (0-1)
            max_tokens: Maximum tokens
            model: Specific model to use (for cloud mode)

        Returns:
            Generated text

        Raises:
            ValueError: If mode unavailable
            RuntimeError: If generation fails
        """
        if mode == ProcessingMode.CLOUD:
            if not self.is_cloud_available():
                raise ValueError("Cloud mode not available. Check CHUTES_API_KEY.")

            logger.info(
                f"Generating using cloud mode (Chutes) with model: {model or 'default'}"
            )
            return self._generate_cloud(
                prompt, system_prompt, temperature, max_tokens, model
            )

        elif mode == ProcessingMode.LOCAL:
            if not self.is_local_available():
                raise ValueError("Local mode not available. Ensure Ollama is running.")

            logger.info("Generating using local mode (Ollama)")
            return self._generate_local(prompt, system_prompt, temperature, max_tokens)

        else:
            raise ValueError(f"Unknown processing mode: {mode}")

    def _generate_cloud(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        model: Optional[str] = None,
    ) -> str:
        """Generate using cloud provider"""
        if not self.cloud_provider:
            raise RuntimeError("Cloud provider not initialized")

        try:
            messages = []
            if system_prompt:
                messages.append(Message(role="system", content=system_prompt))
            messages.append(Message(role="user", content=prompt))

            response = self.cloud_provider.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                model=model,
            )

            return response.content

        except Exception as e:
            logger.error(f"Cloud generation failed: {e}")
            raise RuntimeError(f"Cloud generation failed: {e}")

    def _generate_local(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Generate using local provider"""
        if not self.local_provider:
            raise RuntimeError("Local provider not initialized")

        try:
            return self.local_provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        except Exception as e:
            logger.error(f"Local generation failed: {e}")
            raise RuntimeError(f"Local generation failed: {e}")

    def is_cloud_available(self) -> bool:
        """Check if cloud provider is available"""
        return self.cloud_provider is not None and config.is_cloud_enabled()

    def is_local_available(self) -> bool:
        """Check if local provider is available"""
        if not self.local_provider:
            return False

        return (
            self.local_provider.is_available()
            and self.local_provider.is_model_available()
        )

    def get_available_cloud_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available cloud models with availability status

        Returns:
            List of available cloud models
        """
        if not self.is_cloud_available():
            return []

        # For now, return all configured models as available
        # In a real implementation, you might want to check availability via API
        return [{**model, "available": True} for model in self.AVAILABLE_CLOUD_MODELS]

    def get_available_modes(self) -> List[Dict[str, Any]]:
        """
        Get list of available processing modes

        Returns:
            List of available modes with details
        """
        modes = []

        if self.is_cloud_available():
            cloud_models = self.get_available_cloud_models()
            modes.append(
                {
                    "id": "cloud",
                    "name": "Cloud (Fast)",
                    "description": "Uses Chutes API, requires internet",
                    "available": True,
                    "estimated_speed": "30s per lesson",
                    "provider": "Chutes",
                    "models": cloud_models,
                    "default_model": config.llm.default_model,
                }
            )

        if self.is_local_available():
            if self.local_provider:
                model_info = self.local_provider.get_model_info()
                modes.append(
                    {
                        "id": "local",
                        "name": "Local (Private)",
                        "description": "Uses local Ollama model, no data leaves device",
                        "available": True,
                        "estimated_speed": "90s per lesson",
                        "provider": "Ollama",
                        "model": self.local_provider.model,
                        "model_info": model_info,
                    }
                )
        elif self.local_provider:
            # Ollama configured but not available
            modes.append(
                {
                    "id": "local",
                    "name": "Local (Private)",
                    "description": "Ollama not running or model not installed",
                    "available": False,
                    "provider": "Ollama",
                    "model": self.local_provider.model,
                    "error": "Ollama not running or model not downloaded",
                }
            )

        return modes

    def get_mode_info(self, mode: ProcessingMode) -> Dict[str, Any]:
        """Get information about a specific mode"""
        modes = self.get_available_modes()
        for m in modes:
            if m["id"] == mode.value:
                return m

        return {"id": mode.value, "available": False, "error": "Mode not configured"}

    def is_model_available(self, model_id: str) -> bool:
        """
        Check if a specific cloud model is available

        Args:
            model_id: Model identifier to check

        Returns:
            True if model is available
        """
        if not self.is_cloud_available():
            return False

        available_models = self.get_available_cloud_models()
        return any(
            model["id"] == model_id and model["available"] for model in available_models
        )

    def pull_local_model(self) -> bool:
        """
        Download local model (blocking operation)

        Returns:
            True if successful
        """
        if not self.local_provider:
            logger.error("Local provider not initialized")
            return False

        return self.local_provider.pull_model()

    def list_local_models(self) -> List[str]:
        """List available local models"""
        if not self.local_provider:
            return []

        return self.local_provider.list_available_models()
