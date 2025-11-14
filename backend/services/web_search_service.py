"""Web search service with Brave Search MCP integration and educational filtering"""

import asyncio
import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse

import aiohttp
from asyncio import Lock

from backend.config import config
from backend.utils.error_handling import handle_api_errors, APIFailureError

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Individual search result with educational metadata and citation support"""

    title: str
    url: str
    snippet: str
    domain: str = field(init=False)
    relevance_score: float = 0.0
    educational_domain: bool = False
    # Enhanced citation fields
    citation_id: Optional[str] = None  # Unique identifier for citation tracking
    source_type: str = "web"  # Type of source for citation formatting

    def __post_init__(self):
        """Extract domain from URL and generate citation ID"""
        try:
            parsed_url = urlparse(self.url)
            self.domain = parsed_url.netloc.lower()
            self._check_educational_domain()
            # Generate unique citation ID if not provided
            if not self.citation_id:
                import hashlib

                content_for_id = f"{self.title}{self.url}{self.snippet}"
                self.citation_id = hashlib.md5(content_for_id.encode()).hexdigest()[:12]
        except Exception as e:
            logger.warning(f"Failed to parse URL {self.url}: {e}")
            self.domain = ""
            # Generate fallback citation ID
            if not self.citation_id:
                import hashlib

                self.citation_id = hashlib.md5(self.url.encode()).hexdigest()[:12]

    def _check_educational_domain(self):
        """Check if domain is educational (.edu, .org, etc.)"""
        educational_domains = [".edu", ".org", ".gov"]
        self.educational_domain = any(
            self.domain.endswith(domain) for domain in educational_domains
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "domain": self.domain,
            "relevance_score": self.relevance_score,
            "educational_domain": self.educational_domain,
            "citation_id": self.citation_id,
            "source_type": self.source_type,
        }

    def to_citation_format(self, citation_number: int) -> str:
        """
        Format this search result as a citation string.

        Args:
            citation_number: The citation number to use

        Returns:
            Formatted citation string compatible with IEEE style
        """
        base_citation = f"[{citation_number}] {self.title}"

        # Add domain/URL information for web sources
        if self.url:
            # Extract a clean domain for display
            display_domain = self.domain.replace("www.", "")
            base_citation += f", {display_domain}"

        # Add educational domain indicator if applicable
        if self.educational_domain:
            base_citation += " (Educational)"

        base_citation += f", {self.url}"
        base_citation += "."

        return base_citation

    def to_context_with_citation(self, citation_number: int) -> str:
        """
        Format this search result as context with inline citation.

        Args:
            citation_number: The citation number to use

        Returns:
            Formatted context string with citation marker
        """
        context = (
            f"[Web Source: {citation_number} - {self.domain}]\n"
            f"Title: {self.title}\n"
            f"Content: {self.snippet}\n"
            f"URL: {self.url}\n"
            f"Relevance: {self.relevance_score:.2f}\n"
            f"Reference: [{citation_number}]"
        )

        if self.educational_domain:
            context += f" (Educational Domain)"

        return context


@dataclass
class WebSearchContext:
    """Container for search results and metadata with citation support"""

    query: str
    results: List[SearchResult]
    total_results: int
    search_time: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    educational_filtered: bool = False
    # Citation support fields
    citation_map: Dict[str, int] = field(
        default_factory=dict
    )  # citation_id -> citation_number
    next_citation_number: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "query": self.query,
            "results": [result.to_dict() for result in self.results],
            "total_results": self.total_results,
            "search_time": self.search_time,
            "timestamp": self.timestamp.isoformat(),
            "educational_filtered": self.educational_filtered,
            "citation_map": self.citation_map,
            "next_citation_number": self.next_citation_number,
        }

    def assign_citation_numbers(self) -> None:
        """Assign citation numbers to all results"""
        self.citation_map.clear()
        self.next_citation_number = 1

        for result in self.results:
            if result.citation_id and result.citation_id not in self.citation_map:
                self.citation_map[result.citation_id] = self.next_citation_number
                self.next_citation_number += 1

    def get_citation_number(self, citation_id: Optional[str]) -> Optional[int]:
        """Get citation number for a given citation ID"""
        if not citation_id:
            return None
        return self.citation_map.get(citation_id)

    def get_citation_number_by_url(self, url: str) -> Optional[int]:
        """Get citation number for a result by URL"""
        for result in self.results:
            if result.url == url and result.citation_id:
                return self.citation_map.get(result.citation_id)
        return None

    def format_results_with_citations(self) -> List[str]:
        """Format all results with their citation numbers"""
        if not self.citation_map:
            self.assign_citation_numbers()

        formatted_results = []
        for result in self.results:
            if result.citation_id:  # Check if citation_id exists
                citation_number = self.get_citation_number(result.citation_id)
                if citation_number:
                    formatted_result = result.to_context_with_citation(citation_number)
                    formatted_results.append(formatted_result)

        return formatted_results

    def get_citation_bibliography(self) -> str:
        """Generate bibliography-style citations for all results"""
        if not self.citation_map:
            self.assign_citation_numbers()

        # Sort results by citation number
        def get_sort_key(result):
            if result.citation_id:
                return self.citation_map.get(result.citation_id, 999)
            return 999

        sorted_results = sorted(self.results, key=get_sort_key)

        lines = ["## Web Sources References\n"]
        for result in sorted_results:
            citation_number = self.get_citation_number(result.citation_id)
            if citation_number:
                citation_text = result.to_citation_format(citation_number)
                lines.append(citation_text)

        return "\n".join(lines) if len(lines) > 1 else ""


@dataclass
class CacheEntry:
    """Cached search result with timestamp"""

    key: str
    context: WebSearchContext
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def is_valid(self, ttl_seconds: int) -> bool:
        """Check if cache entry is still valid"""
        expiry_time = self.timestamp + timedelta(seconds=ttl_seconds)
        return datetime.utcnow() < expiry_time


class WebSearchService:
    """
    Async web search service with educational query optimization and caching.

    Integrates with Brave Search MCP tools to provide educational content
    filtering, relevance scoring, and efficient caching.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_ttl: Optional[int] = None,
        max_cache_size: Optional[int] = None,
        timeout: Optional[int] = None,
        educational_only: Optional[bool] = None,
        min_relevance_score: Optional[float] = None,
    ):
        """
        Initialize WebSearchService

        Args:
            api_key: Brave Search API key (defaults to config)
            cache_ttl: Cache time-to-live in seconds (defaults to config)
            max_cache_size: Maximum number of cached entries (defaults to config)
            timeout: Request timeout in seconds (defaults to config)
            educational_only: Filter to educational domains only (defaults to config)
            min_relevance_score: Minimum relevance score threshold (defaults to config)
        """
        # Use centralized config if no overrides provided
        search_config = config.web_search

        self.api_key = api_key or search_config.api_key
        self.cache_ttl = cache_ttl or search_config.cache_ttl
        self.max_cache_size = max_cache_size or search_config.max_cache_size
        self.timeout = timeout or search_config.timeout
        self.educational_only = (
            educational_only
            if educational_only is not None
            else search_config.educational_only
        )
        self.min_relevance_score = (
            min_relevance_score or search_config.min_relevance_score
        )

        # In-memory cache with LRU-like behavior
        self._cache: Dict[str, CacheEntry] = {}
        self._cache_lock = Lock()

        # Educational keywords for relevance scoring
        self._educational_keywords = {
            "teaching",
            "education",
            "learning",
            "curriculum",
            "lesson",
            "pedagogy",
            "instruction",
            "classroom",
            "student",
            "academic",
            "music education",
            "music theory",
            "music pedagogy",
            "music lesson",
            "musical development",
            "music curriculum",
            "teaching music",
        }

        if not self.api_key:
            logger.warning("Brave Search API key not configured")

    async def search_educational_resources(
        self,
        query: str,
        max_results: int = 10,
        grade_level: Optional[str] = None,
        subject: Optional[str] = None,
    ) -> Optional[WebSearchContext]:
        """
        Search for educational resources with query optimization

        Args:
            query: Search query
            max_results: Maximum number of results to return
            grade_level: Optional grade level for context
            subject: Optional subject for context

        Returns:
            WebSearchContext with filtered results or None on failure
        """
        try:
            # Check cache first
            cache_key = self._get_cache_key(query, max_results, grade_level, subject)
            cached_entry = await self._get_from_cache(cache_key)
            if cached_entry:
                logger.info(f"Cache hit for query: {query}")
                return cached_entry.context

            # Build educational query
            optimized_query = self._build_educational_query(query, grade_level, subject)

            # Execute search
            start_time = time.time()
            raw_results = await self._execute_brave_search(optimized_query, max_results)
            search_time = time.time() - start_time

            if not raw_results:
                logger.warning(f"No results returned for query: {query}")
                return None

            # Convert to SearchResult objects
            search_results = []
            for result_data in raw_results:
                result = SearchResult(
                    title=result_data.get("title", ""),
                    url=result_data.get("url", ""),
                    snippet=result_data.get("snippet", ""),
                )
                search_results.append(result)

            # Filter and score results
            filtered_results = self._filter_educational_results(search_results)
            scored_results = self._score_educational_relevance(
                filtered_results, query, grade_level, subject
            )

            # Remove results below relevance threshold
            final_results = [
                result
                for result in scored_results
                if result.relevance_score >= self.min_relevance_score
            ]

            # Create context
            context = WebSearchContext(
                query=query,
                results=final_results[:max_results],
                total_results=len(final_results),
                search_time=search_time,
                educational_filtered=self.educational_only,
            )

            # Assign citation numbers to results
            context.assign_citation_numbers()

            # Cache the result
            await self._cache_result(cache_key, context)

            logger.info(
                f"Search completed: {len(final_results)} results in {search_time:.2f}s"
            )
            return context

        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return None

    def _build_educational_query(
        self,
        query: str,
        grade_level: Optional[str] = None,
        subject: Optional[str] = None,
    ) -> str:
        """
        Build optimized query for educational content

        Args:
            query: Original query
            grade_level: Optional grade level
            subject: Optional subject

        Returns:
            Optimized query string
        """
        educational_terms = []

        # Add educational context
        if subject or "music" in query.lower():
            educational_terms.append("music education")

        if grade_level:
            educational_terms.append(f"{grade_level} OR elementary education")

        # Add domain filtering if enabled
        if self.educational_only:
            educational_terms.append("site:.edu OR site:.org")

        # Combine with original query
        if educational_terms:
            optimized_query = f"{query} {' '.join(educational_terms)}"
        else:
            optimized_query = query

        logger.debug(f"Optimized query: {optimized_query}")
        return optimized_query

    def _filter_educational_results(
        self, results: List[SearchResult]
    ) -> List[SearchResult]:
        """
        Filter results for educational content

        Args:
            results: List of search results

        Returns:
            Filtered list of results
        """
        filtered = []

        for result in results:
            include = True

            # Check educational domain preference
            if self.educational_only and not result.educational_domain:
                include = False

            # Check for educational content indicators
            if include:
                text_lower = f"{result.title} {result.snippet}".lower()
                educational_indicators = {
                    "lesson plan",
                    "teaching",
                    "education",
                    "curriculum",
                    "activity",
                    "assessment",
                    "learning objective",
                    "music teacher",
                    "classroom",
                    "student",
                }

                # If not educational domain, check content indicators
                if not result.educational_domain:
                    has_educational_content = any(
                        indicator in text_lower for indicator in educational_indicators
                    )
                    if not has_educational_content:
                        include = False

            if include:
                filtered.append(result)

        logger.debug(f"Filtered {len(results)} -> {len(filtered)} results")
        return filtered

    def _score_educational_relevance(
        self,
        results: List[SearchResult],
        query: str,
        grade_level: Optional[str] = None,
        subject: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        Score results for educational relevance

        Args:
            results: List of search results
            query: Original query
            grade_level: Optional grade level
            subject: Optional subject

        Returns:
            Results with relevance scores
        """
        query_terms = set(query.lower().split())
        if subject:
            query_terms.update(subject.lower().split())
        if grade_level:
            query_terms.update(grade_level.lower().split())

        for result in results:
            score = 0.0
            text_lower = f"{result.title} {result.snippet}".lower()

            # Educational domain bonus
            if result.educational_domain:
                score += 0.3

            # Educational keyword matching
            keyword_matches = sum(
                1 for keyword in self._educational_keywords if keyword in text_lower
            )
            score += min(keyword_matches * 0.1, 0.4)

            # Query term matching
            query_matches = sum(1 for term in query_terms if term in text_lower)
            score += min(query_matches * 0.15, 0.3)

            result.relevance_score = min(score, 1.0)

        # Sort by relevance score
        return sorted(results, key=lambda x: x.relevance_score, reverse=True)

    @handle_api_errors
    async def _execute_brave_search(
        self, query: str, max_results: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Execute search using Brave Search MCP client

        Args:
            query: Search query
            max_results: Maximum results requested

        Returns:
            Raw search results or None on failure
        """
        if not self.api_key:
            raise APIFailureError("Brave Search API key not configured")

        # Use MCP client transport via stdio
        # For now, implement direct HTTP client as fallback
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key,
        }

        params = {
            "q": query,
            "count": max_results,
            "source": "web",
            "text_decorations": "false",
            "spellcheck": "true",
            "result_filter": "news,web",
            "safesearch": "moderate",
            "freshness": "pw",  # Past week
        }

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                async with session.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    headers=headers,
                    params=params,
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("web", {}).get("results", [])
                    else:
                        logger.error(f"Brave Search API error: {response.status}")
                        return None

        except asyncio.TimeoutError:
            logger.error(f"Search timeout for query: {query}")
            return None
        except Exception as e:
            logger.error(f"Search execution failed: {e}")
            return None

    def _get_cache_key(
        self,
        query: str,
        max_results: int,
        grade_level: Optional[str] = None,
        subject: Optional[str] = None,
    ) -> str:
        """
        Generate cache key for search parameters

        Args:
            query: Search query
            max_results: Maximum results
            grade_level: Optional grade level
            subject: Optional subject

        Returns:
            Cache key string
        """
        key_components = [
            query.lower(),
            str(max_results),
            str(self.educational_only),
            str(self.min_relevance_score),
        ]

        if grade_level:
            key_components.append(f"grade:{grade_level.lower()}")
        if subject:
            key_components.append(f"subject:{subject.lower()}")

        key_string = "|".join(key_components)
        return hashlib.md5(key_string.encode()).hexdigest()

    async def _get_from_cache(self, cache_key: str) -> Optional[CacheEntry]:
        """
        Get cached result if valid

        Args:
            cache_key: Cache key to retrieve

        Returns:
            CacheEntry if valid, None otherwise
        """
        async with self._cache_lock:
            entry = self._cache.get(cache_key)
            if entry and entry.is_valid(self.cache_ttl):
                return entry
            elif entry:
                # Remove expired entry
                del self._cache[cache_key]

        return None

    async def _cache_result(self, cache_key: str, context: WebSearchContext) -> None:
        """
        Cache search result with LRU eviction

        Args:
            cache_key: Cache key for storage
            context: Search context to cache
        """
        async with self._cache_lock:
            # Remove oldest entries if cache is full
            while len(self._cache) >= self.max_cache_size:
                oldest_key = min(
                    self._cache.keys(), key=lambda k: self._cache[k].timestamp
                )
                del self._cache[oldest_key]

            # Add new entry
            self._cache[cache_key] = CacheEntry(key=cache_key, context=context)

    async def clear_cache(self) -> None:
        """Clear all cached results"""
        async with self._cache_lock:
            self._cache.clear()
        logger.info("Search cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self._cache),
            "max_cache_size": self.max_cache_size,
            "cache_ttl": self.cache_ttl,
            "educational_only": self.educational_only,
            "min_relevance_score": self.min_relevance_score,
        }
