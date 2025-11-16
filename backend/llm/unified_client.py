"""Unified LLM client with fallback support for Chutes and Ollama"""

import logging
from typing import List, Dict, Any, Optional, Iterator, Union
from dataclasses import dataclass
from enum import Enum

from .chutes_client import ChutesClient, Message, ChatResponse
from .local_provider import OllamaProvider
from .model_router import ProcessingMode, ModelRouter
from backend.config import config

logger = logging.getLogger(__name__)


class ClientType(str, Enum):
    """Available client types"""

    CHUTES = "chutes"
    OLLAMA = "ollama"
    AUTO = "auto"  # Automatically choose based on availability


@dataclass
class ClientConfig:
    """Configuration for LLM client"""

    preferred_client: ClientType = ClientType.AUTO
    fallback_enabled: bool = True
    timeout: int = 120
    max_retries: int = 3


class UnifiedLLMClient:
    """
    Unified LLM client that supports both Chutes and Ollama with automatic fallback

    This client solves the initialization problem by:
    1. Not raising errors during construction
    2. Lazily initializing clients when actually needed
    3. Providing automatic fallback between providers
    4. Supporting both cloud and local modes
    """

    def __init__(self, client_config: Optional[ClientConfig] = None):
        """
        Initialize unified client

        Args:
            client_config: Client configuration (defaults to AUTO with fallback)
        """
        self.config = client_config or ClientConfig()
        self._chutes_client: Optional[ChutesClient] = None
        self._ollama_provider: Optional[OllamaProvider] = None
        self._model_router: Optional[ModelRouter] = None
        self._initialized_clients: Dict[ClientType, bool] = {
            ClientType.CHUTES: False,
            ClientType.OLLAMA: False,
        }

        # Don't initialize clients during construction
        # They will be initialized lazily when needed
        logger.info("Unified LLM client initialized (lazy loading enabled)")

    def _get_chutes_client(self) -> Optional[ChutesClient]:
        """Get Chutes client, initializing if necessary"""
        if not self._initialized_clients[ClientType.CHUTES]:
            try:
                if config.is_cloud_enabled():
                    self._chutes_client = ChutesClient()
                    self._initialized_clients[ClientType.CHUTES] = True
                    logger.info("Chutes client initialized successfully")
                else:
                    logger.info("Chutes client not available (no API key)")
            except Exception as e:
                logger.warning(f"Failed to initialize Chutes client: {e}")
                self._initialized_clients[ClientType.CHUTES] = False

        return self._chutes_client

    def _get_ollama_provider(self) -> Optional[OllamaProvider]:
        """Get Ollama provider, initializing if necessary"""
        if not self._initialized_clients[ClientType.OLLAMA]:
            try:
                self._ollama_provider = OllamaProvider()
                self._initialized_clients[ClientType.OLLAMA] = True
                logger.info("Ollama provider initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Ollama provider: {e}")
                self._initialized_clients[ClientType.OLLAMA] = False

        return self._ollama_provider

    def _get_model_router(self) -> ModelRouter:
        """Get model router, initializing if necessary"""
        if self._model_router is None:
            self._model_router = ModelRouter()
            logger.info("Model router initialized")

        return self._model_router

    def _choose_client(self) -> Union[ChutesClient, OllamaProvider]:
        """
        Choose the appropriate client based on configuration and availability

        Returns:
            Available client instance

        Raises:
            RuntimeError: If no suitable client is available
        """
        if self.config.preferred_client == ClientType.CHUTES:
            chutes = self._get_chutes_client()
            if chutes:
                return chutes
            elif not self.config.fallback_enabled:
                raise RuntimeError("Chutes client not available and fallback disabled")

        elif self.config.preferred_client == ClientType.OLLAMA:
            ollama = self._get_ollama_provider()
            if ollama and ollama.is_available() and ollama.is_model_available():
                return ollama
            elif not self.config.fallback_enabled:
                raise RuntimeError(
                    "Ollama provider not available and fallback disabled"
                )

        # AUTO mode or fallback - try Chutes first, then Ollama
        chutes = self._get_chutes_client()
        if chutes:
            return chutes

        ollama = self._get_ollama_provider()
        if ollama and ollama.is_available() and ollama.is_model_available():
            return ollama

        raise RuntimeError(
            "No LLM client available. Please configure CHUTES_API_KEY or ensure Ollama is running."
        )

    def chat_completion(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> ChatResponse:
        """
        Create a chat completion using the best available client

        Args:
            messages: List of chat messages
            model: Model to use (optional)
            temperature: Sampling temperature (optional)
            max_tokens: Maximum tokens to generate (optional)
            **kwargs: Additional parameters

        Returns:
            ChatResponse with generated content
        """
        client = self._choose_client()

        if isinstance(client, ChutesClient):
            return client.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
        elif isinstance(client, OllamaProvider):
            # Convert Message format to Ollama format
            system_prompt = None
            user_prompt = ""

            for msg in messages:
                if msg.role == "system":
                    system_prompt = (
                        msg.content
                        if isinstance(msg.content, str)
                        else str(msg.content)
                    )
                elif msg.role == "user":
                    user_prompt = (
                        msg.content
                        if isinstance(msg.content, str)
                        else str(msg.content)
                    )

            generated_text = client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=temperature or 0.7,
                max_tokens=max_tokens or 2000,
            )

            # Return ChatResponse-like object
            return ChatResponse(
                content=generated_text,
                model=client.model,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                finish_reason="stop",
            )
        else:
            raise RuntimeError(f"Unknown client type: {type(client)}")

    def chat_completion_stream(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Iterator[str]:
        """
        Create a streaming chat completion

        Args:
            messages: List of chat messages
            model: Model to use (optional)
            temperature: Sampling temperature (optional)
            max_tokens: Maximum tokens to generate (optional)
            **kwargs: Additional parameters

        Yields:
            Content chunks as they are generated
        """
        client = self._choose_client()

        if isinstance(client, ChutesClient):
            yield from client.chat_completion_stream(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
        elif isinstance(client, OllamaProvider):
            # Convert Message format to Ollama format
            system_prompt = None
            user_prompt = ""

            for msg in messages:
                if msg.role == "system":
                    system_prompt = (
                        msg.content
                        if isinstance(msg.content, str)
                        else str(msg.content)
                    )
                elif msg.role == "user":
                    user_prompt = (
                        msg.content
                        if isinstance(msg.content, str)
                        else str(msg.content)
                    )

            # Use async streaming from Ollama
            import asyncio

            async def stream_generator():
                async for chunk in client.generate_stream(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    temperature=temperature or 0.7,
                    max_tokens=max_tokens or 2000,
                ):
                    yield chunk

            # Run async generator in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                for chunk in loop.run_until_complete(stream_generator().__anext__()):
                    yield chunk
            except StopAsyncIteration:
                pass
            finally:
                loop.close()
        else:
            raise RuntimeError(f"Unknown client type: {type(client)}")

    def create_embedding(self, text: str, model: Optional[str] = None) -> List[float]:
        """
        Create an embedding for the given text

        Args:
            text: Text to embed
            model: Embedding model to use (optional)

        Returns:
            List of floats representing the embedding vector
        """
        # Only Chutes supports embeddings currently
        chutes = self._get_chutes_client()
        if chutes:
            return chutes.create_embedding(text, model)
        else:
            raise RuntimeError("Embeddings only available with Chutes client")

    def create_embeddings_batch(
        self, texts: List[str], model: Optional[str] = None
    ) -> List[List[float]]:
        """
        Create embeddings for multiple texts

        Args:
            texts: List of texts to embed
            model: Embedding model to use (optional)

        Returns:
            List of embedding vectors
        """
        # Only Chutes supports embeddings currently
        chutes = self._get_chutes_client()
        if chutes:
            return chutes.create_embeddings_batch(texts, model)
        else:
            raise RuntimeError("Embeddings only available with Chutes client")

    def get_available_clients(self) -> Dict[str, Any]:
        """
        Get information about available clients

        Returns:
            Dictionary with client availability information
        """
        chutes_available = self._get_chutes_client() is not None
        ollama_provider = self._get_ollama_provider()
        ollama_available = (
            ollama_provider is not None
            and ollama_provider.is_available()
            and ollama_provider.is_model_available()
        )

        return {
            "chutes": {
                "available": chutes_available,
                "name": "Chutes (Cloud)",
                "description": "Fast cloud-based LLM with embeddings support",
            },
            "ollama": {
                "available": ollama_available,
                "name": "Ollama (Local)",
                "description": "Private local LLM processing",
                "model": ollama_provider.model if ollama_provider else None,
            },
            "preferred": self.config.preferred_client.value,
            "fallback_enabled": self.config.fallback_enabled,
        }

    def is_available(self) -> bool:
        """Check if any client is available"""
        try:
            self._choose_client()
            return True
        except RuntimeError:
            return False


# Convenience function for backward compatibility
def create_llm_client(
    client_type: ClientType = ClientType.AUTO, fallback_enabled: bool = True
) -> UnifiedLLMClient:
    """
    Create an LLM client with the specified configuration

    Args:
        client_type: Preferred client type
        fallback_enabled: Whether to enable fallback to other clients

    Returns:
        Configured UnifiedLLMClient instance
    """
    config = ClientConfig(
        preferred_client=client_type, fallback_enabled=fallback_enabled
    )
    return UnifiedLLMClient(config)


# Default client for easy import
default_client = UnifiedLLMClient()
