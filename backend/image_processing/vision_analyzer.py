"""Vision analyzer using Chutes Vision API for semantic understanding"""

import requests
import base64
from pathlib import Path
from typing import Optional, Dict
import os
import logging

from ..config import config

logger = logging.getLogger(__name__)


class VisionAnalyzer:
    """
    Analyzes images using vision AI models

    Provides semantic understanding of visual content beyond OCR
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base_url: Optional[str] = None
    ):
        """
        Initialize vision analyzer

        Args:
            api_key: Chutes API key (or from env)
            api_base_url: Chutes API base URL (or from env)
        """
        self.api_key = api_key or config.chutes.api_key
        self.api_base_url = api_base_url or config.chutes.base_url

        if not self.api_key:
            logger.warning("CHUTES_API_KEY not set, vision analysis will be disabled")

    def analyze_image(
        self,
        image_path: str,
        prompt: str = "Describe this image in detail, focusing on any musical notation, instruments, educational content, or instructional diagrams."
    ) -> Optional[str]:
        """
        Analyze image using vision model

        Args:
            image_path: Path to image file
            prompt: Analysis prompt for the vision model

        Returns:
            Analysis text or None if failed
        """
        if not self.api_key:
            logger.warning("Vision analysis skipped: API key not configured")
            return None

        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

            # Determine image format
            suffix = Path(image_path).suffix.lower()
            mime_type = self._get_mime_type(suffix)

            # Call Chutes Vision API
            response = requests.post(
                f"{self.api_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "Qwen/Qwen3-VL-235B-A22B-Instruct",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{mime_type};base64,{image_data}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 500,
                    "temperature": 0.3
                },
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            # Extract analysis from response
            analysis = result['choices'][0]['message']['content']

            logger.info(f"Vision analysis completed: {len(analysis)} characters")
            return analysis

        except requests.exceptions.RequestException as e:
            logger.error(f"Vision API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            return None

    def analyze_sheet_music(self, image_path: str) -> Optional[Dict[str, str]]:
        """
        Specialized analysis for sheet music

        Args:
            image_path: Path to sheet music image

        Returns:
            Dictionary with musical elements or None
        """
        prompt = """Analyze this sheet music image and provide:
1. Composer and title (if visible)
2. Time signature
3. Key signature
4. Tempo markings
5. Notable musical elements (dynamics, articulations, etc.)
6. Difficulty level estimate
7. Musical period or style

Format the response as a structured analysis."""

        analysis = self.analyze_image(image_path, prompt)

        if analysis:
            return {
                "type": "sheet_music",
                "analysis": analysis
            }
        return None

    def analyze_diagram(self, image_path: str) -> Optional[Dict[str, str]]:
        """
        Specialized analysis for instructional diagrams

        Args:
            image_path: Path to diagram image

        Returns:
            Dictionary with diagram elements or None
        """
        prompt = """Analyze this educational diagram and provide:
1. Main topic or concept being illustrated
2. Key visual elements and their relationships
3. Any text labels or annotations
4. Educational purpose or learning objective
5. Target audience level (beginner, intermediate, advanced)

Format the response as a structured analysis."""

        analysis = self.analyze_image(image_path, prompt)

        if analysis:
            return {
                "type": "instructional_diagram",
                "analysis": analysis
            }
        return None

    def extract_elements(self, image_path: str) -> Optional[Dict[str, list]]:
        """
        Extract specific elements from image

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with categorized elements or None
        """
        prompt = """List all distinct elements in this image:
- Musical instruments (if any)
- Musical notation elements (notes, rests, clefs, etc.)
- Text labels and annotations
- Diagrams or charts
- People or performers
- Educational symbols

Provide a structured list."""

        analysis = self.analyze_image(image_path, prompt)

        if analysis:
            # Parse elements from analysis
            # This is a simplified version; could be enhanced with structured output
            return {
                "elements": [line.strip() for line in analysis.split('\n') if line.strip()],
                "raw_analysis": analysis
            }
        return None

    def _get_mime_type(self, suffix: str) -> str:
        """Get MIME type from file suffix"""
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff'
        }
        return mime_types.get(suffix, 'image/jpeg')

    def is_available(self) -> bool:
        """Check if vision analysis is available"""
        return bool(self.api_key)
