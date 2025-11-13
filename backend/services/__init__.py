"""Services module for PocketMusec backend"""

from .web_search_service import WebSearchService, SearchResult, WebSearchContext, CacheEntry

__all__ = [
    'WebSearchService',
    'SearchResult', 
    'WebSearchContext',
    'CacheEntry'
]