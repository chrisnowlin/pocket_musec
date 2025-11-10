"""Chutes API client for LLM interactions"""

import requests
import json
import time
from typing import List, Dict, Any, Optional, Iterator, Union
from dataclasses import dataclass
import logging

from backend.config import config
from backend.llm.prompt_templates import LessonPromptContext, LessonPromptTemplates
from backend.utils.error_handling import handle_api_errors, APIFailureError

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Chat message"""
    role: str  # 'system', 'user', or 'assistant'
    content: str


@dataclass
class ChatResponse:
    """Response from chat completion"""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str


class ChutesAPIError(Exception):
    """Base exception for Chutes API errors"""
    pass


class ChutesAuthenticationError(ChutesAPIError):
    """Authentication failed"""
    pass


class ChutesRateLimitError(ChutesAPIError):
    """Rate limit exceeded"""
    pass


class ChutesClient:
    """Client for Chutes AI API"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        timeout: int = 120,
        max_retries: int = 3,
    ):
        self.api_key = api_key or config.CHUTES_API_KEY
        self.base_url = (base_url or config.CHUTES_API_BASE_URL).rstrip('/')
        self.default_model = default_model or config.DEFAULT_MODEL
        self.embedding_model = config.EMBEDDING_MODEL
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_delay = 1.0  # Base delay for rate limiting
        
        if not self.api_key:
            raise ChutesAuthenticationError(
                "CHUTES_API_KEY not found. Please set it in .env file."
            )
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> requests.Response:
        """Make HTTP request with retry logic"""
        url = f"{self.base_url}{endpoint}"
        headers = kwargs.pop('headers', {})
        headers['Authorization'] = f'Bearer {self.api_key}'
        headers['Content-Type'] = 'application/json'
        
        for attempt in range(self.max_retries):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    timeout=self.timeout,
                    **kwargs
                )
                
                # Handle rate limiting with exponential backoff
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 2 ** attempt))
                    logger.warning(f"Rate limited. Retrying after {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                
                # Handle authentication errors
                if response.status_code == 401:
                    raise ChutesAuthenticationError("Invalid API key")
                
                # Raise for other errors
                response.raise_for_status()
                
                return response
                
            except requests.exceptions.Timeout:
                if attempt == self.max_retries - 1:
                    raise ChutesAPIError(f"Request timed out after {self.timeout}s")
                logger.warning(f"Timeout on attempt {attempt + 1}, retrying...")
                time.sleep(2 ** attempt)
                
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise ChutesAPIError(f"Request failed: {str(e)}")
                logger.warning(f"Request failed on attempt {attempt + 1}, retrying...")
                time.sleep(2 ** attempt)
        
        raise ChutesAPIError("Max retries exceeded")
    
    @handle_api_errors
    def chat_completion(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        """
        Create a chat completion
        
        Args:
            messages: List of chat messages
            model: Model to use (defaults to config.DEFAULT_MODEL)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters to pass to the API
        
        Returns:
            ChatResponse with generated content
        """
        payload = {
            'model': model or self.default_model,
            'messages': [{'role': msg.role, 'content': msg.content} for msg in messages],
            'temperature': temperature or config.DEFAULT_TEMPERATURE,
            'max_tokens': max_tokens or config.DEFAULT_MAX_TOKENS,
            **kwargs
        }
        
        response = self._make_request('POST', '/chat/completions', json=payload)
        data = response.json()
        
        choice = data['choices'][0]
        return ChatResponse(
            content=choice['message']['content'],
            model=data['model'],
            usage=data.get('usage', {}),
            finish_reason=choice.get('finish_reason', 'unknown')
        )
    
    def chat_completion_stream(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Iterator[str]:
        """
        Create a streaming chat completion
        
        Args:
            messages: List of chat messages
            model: Model to use (defaults to config.DEFAULT_MODEL)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters to pass to the API
        
        Yields:
            Content chunks as they are generated
        """
        payload = {
            'model': model or self.default_model,
            'messages': [{'role': msg.role, 'content': msg.content} for msg in messages],
            'temperature': temperature or config.DEFAULT_TEMPERATURE,
            'max_tokens': max_tokens or config.DEFAULT_MAX_TOKENS,
            'stream': True,
            **kwargs
        }
        
        response = self._make_request('POST', '/chat/completions', json=payload, stream=True)
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]  # Remove 'data: ' prefix
                    if data_str == '[DONE]':
                        break
                    
                    try:
                        data = json.loads(data_str)
                        if 'choices' in data and len(data['choices']) > 0:
                            delta = data['choices'][0].get('delta', {})
                            if 'content' in delta:
                                yield delta['content']
                    except json.JSONDecodeError:
                        continue
    
    def create_embedding(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """
        Create an embedding for the given text
        
        Args:
            text: Text to embed
            model: Embedding model to use (defaults to config.EMBEDDING_MODEL)
        
        Returns:
            List of floats representing the embedding vector
        """
        payload = {
            'model': model or config.EMBEDDING_MODEL,
            'input': text
        }
        
        # Use dedicated embedding endpoint
        embedding_url = config.CHUTES_EMBEDDING_BASE_URL.rstrip('/')
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f"{embedding_url}/embeddings",
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        data = response.json()
        
        return data['data'][0]['embedding']
    
    def create_embeddings_batch(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """
        Create embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            model: Embedding model to use (defaults to config.EMBEDDING_MODEL)
        
        Returns:
            List of embedding vectors
        """
        payload = {
            'model': model or config.EMBEDDING_MODEL,
            'input': texts
        }
        
        # Use dedicated embedding endpoint
        embedding_url = config.CHUTES_EMBEDDING_BASE_URL.rstrip('/')
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f"{embedding_url}/embeddings",
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        data = response.json()
        
        # Sort by index to maintain order
        sorted_embeddings = sorted(data['data'], key=lambda x: x['index'])
        return [item['embedding'] for item in sorted_embeddings]
    
    def generate_lesson_plan(
        self,
        context: LessonPromptContext,
        template_type: str = "lesson_plan",
        stream: bool = False,
        **kwargs
    ) -> Union[str, Iterator[str]]:
        """
        Generate a lesson plan using the specified template
        
        Args:
            context: Lesson context information
            template_type: Type of template to use
            stream: Whether to stream the response
            **kwargs: Additional parameters for the API call
            
        Returns:
            Generated lesson plan content
        """
        messages = self._prepare_messages(context, template_type)
        
        if stream:
            return self.chat_completion_stream(
                messages=messages,
                **kwargs
            )
        else:
            response = self.chat_completion(
                messages=messages,
                **kwargs
            )
            return response.content
    
    def generate_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (alias for create_embeddings_batch)
        
        Args:
            texts: List of texts to embed
            model: Embedding model to use
            
        Returns:
            List of embedding vectors
        """
        return self.create_embeddings_batch(texts, model)
    
    def _prepare_messages(
        self,
        context: LessonPromptContext,
        template_type: str = "lesson_plan"
    ) -> List[Message]:
        """
        Prepare messages for API call using templates
        
        Args:
            context: Lesson context information
            template_type: Type of template to use
            
        Returns:
            List of messages for the API call
        """
        system_prompt = LessonPromptTemplates.get_system_prompt()
        user_prompt = LessonPromptTemplates.generate_prompt(template_type, context)
        
        return [
            Message(role='system', content=system_prompt),
            Message(role='user', content=user_prompt)
        ]
    
    def build_prompt_context(self, standard_data: Dict[str, Any]) -> LessonPromptContext:
        """
        Build LessonPromptContext from standard data dictionary
        
        Args:
            standard_data: Dictionary containing standard information
            
        Returns:
            LessonPromptContext instance
        """
        return LessonPromptContext(
            grade_level=standard_data.get("grade_level"),
            strand_code=standard_data.get("strand_code"),
            strand_name=standard_data.get("strand_name"),
            strand_description=standard_data.get("strand_description"),
            standard_id=standard_data.get("standard_id"),
            standard_text=standard_data.get("standard_text"),
            objectives=standard_data.get("objectives", []),
            additional_context=standard_data.get("additional_context"),
            lesson_duration=standard_data.get("lesson_duration"),
            class_size=standard_data.get("class_size"),
            available_resources=standard_data.get("available_resources")
        )


# Convenience function for simple use cases
def ask_llm(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> str:
    """
    Simple wrapper for asking the LLM a question
    
    Args:
        prompt: User prompt/question
        system_prompt: Optional system prompt to set context
        model: Model to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
    
    Returns:
        String response from the LLM
    """
    client = ChutesClient()
    messages = []
    
    if system_prompt:
        messages.append(Message(role='system', content=system_prompt))
    
    messages.append(Message(role='user', content=prompt))
    
    response = client.chat_completion(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )
    
    return response.content
