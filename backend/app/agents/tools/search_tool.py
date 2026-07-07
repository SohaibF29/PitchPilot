"""
Tavily Search Tool wrapper for Market Analyst.
"""

from __future__ import annotations

import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)


from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper

def get_tavily_tool(api_key: str) -> TavilySearchResults:
    """
    Returns a configured TavilySearchResults tool for LangChain agents.
    Uses the decrypted user API key from the database.
    """
    api_wrapper = TavilySearchAPIWrapper(tavily_api_key=api_key)
    return TavilySearchResults(
        api_wrapper=api_wrapper,
        max_results=5,
        search_depth="advanced",
        include_answer=True,
    )
