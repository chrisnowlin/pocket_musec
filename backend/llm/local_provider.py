"""Local LLM provider using Ollama"""

import requests
import json
from typing import Optional, Dict, AsyncIterator
import logging

logger = logging.getLogger(__name__)


class OllamaProvider:
    """
    Local LLM provider using Ollama

    Provides interface to local models (Qwen3 8B, Llama, etc.)
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """
        Initialize Ollama provider

        Args:
            base_url: Ollama API URL (defaults to config)
            model: Model name (defaults to config)
            timeout: Request timeout in seconds (defaults to config)
        """
        # Use centralized config if no overrides provided
        from ..config import config
        self.base_url = base_url or config.ollama.base_url
        self.model = model or config.ollama.model
        self.timeout = timeout or config.ollama.timeout

    def is_available(self) -> bool:
        """
        Check if Ollama is available

        Returns:
            True if Ollama server is running
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            return False

    def is_model_available(self) -> bool:
        """
        Check if configured model is installed

        Returns:
            True if model is available
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                models = [m['name'] for m in data.get('models', [])]
                return self.model in models or f"{self.model}:latest" in models

            return False

        except Exception as e:
            logger.error(f"Failed to check model availability: {e}")
            return False

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Generate text using Ollama

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Temperature (0-1)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text

        Raises:
            ConnectionError: If Ollama not available
            RuntimeError: If generation fails
        """
        if not self.is_available():
            raise ConnectionError("Ollama server not available at " + self.base_url)

        if not self.is_model_available():
            raise RuntimeError(f"Model {self.model} not installed. Run: ollama pull {self.model}")

        try:
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Call Ollama API
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                },
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            # Extract generated text
            generated_text = result['message']['content']

            logger.info(f"Generated {len(generated_text)} characters using {self.model}")

            return generated_text

        except requests.exceptions.Timeout:
            raise RuntimeError(f"Generation timed out after {self.timeout}s")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama API error: {e}")
        except Exception as e:
            raise RuntimeError(f"Generation failed: {e}")

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncIterator[str]:
        """
        Generate text with streaming (async)

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Temperature
            max_tokens: Maximum tokens

        Yields:
            Generated text chunks

        Raises:
            ConnectionError: If Ollama not available
            RuntimeError: If generation fails
        """
        if not self.is_available():
            raise ConnectionError("Ollama server not available")

        if not self.is_model_available():
            raise RuntimeError(f"Model {self.model} not installed")

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            # Stream response
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                },
                stream=True,
                timeout=self.timeout
            )

            response.raise_for_status()

            # Process streaming chunks
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if 'message' in chunk and 'content' in chunk['message']:
                            yield chunk['message']['content']

                        # Check if done
                        if chunk.get('done', False):
                            break

                    except json.JSONDecodeError:
                        continue

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Streaming failed: {e}")

    def get_model_info(self) -> Optional[Dict]:
        """
        Get information about the loaded model

        Returns:
            Model information dictionary or None
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"name": self.model},
                timeout=5
            )

            if response.status_code == 200:
                return response.json()

            return None

        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return None

    def pull_model(self) -> bool:
        """
        Download/pull the model (blocking operation)

        Returns:
            True if successful

        Note: This can take a long time (GB download)
        """
        try:
            logger.info(f"Pulling model {self.model}...")

            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": self.model},
                stream=True,
                timeout=None  # No timeout for download
            )

            response.raise_for_status()

            # Stream progress
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        status = data.get('status', '')
                        logger.info(f"Pull progress: {status}")
                    except json.JSONDecodeError:
                        continue

            logger.info(f"Model {self.model} pulled successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to pull model: {e}")
            return False

    def list_available_models(self) -> list:
        """
        List all installed models

        Returns:
            List of model names
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                return [m['name'] for m in data.get('models', [])]

            return []

        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
