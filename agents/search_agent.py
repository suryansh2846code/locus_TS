# search_agent.py
# Agent specialized in web searching and data gathering.
# Can be hired to find specific information.

from .base_agent import BaseAgent

class SearchAgent(BaseAgent):
    def execute_task(self, query):
        """Performs a web search using Brave/Exa/Tavily via Locus."""
        pass
