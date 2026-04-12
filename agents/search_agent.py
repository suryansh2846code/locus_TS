"""
agents/search_agent.py
───────────────────────
Specialist agent that searches the web for real-time information using the
Brave Search Wrapped API via Locus.

Locus endpoint used:
  POST https://beta-api.paywithlocus.com/api/wrapped/brave/web-search
  Estimated cost: ~$0.035 per call (billed from Locus wallet in USDC)

Docs: https://beta.paywithlocus.com/wapi/brave.md
"""

from __future__ import annotations

import os
import sys
import requests
from dotenv import load_dotenv

# Support both package import (from agents.search_agent) 
# and direct script execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent

load_dotenv()

# ── Locus API config ────────────────────────────────────────────────────────
_LOCUS_API_KEY  = os.getenv("LOCUS_API_KEY", "")
_BRAVE_ENDPOINT = "https://beta-api.paywithlocus.com/api/wrapped/brave/web-search"
_DEFAULT_COUNT  = 5     # results per search (1-20)


class SearchAgent(BaseAgent):
    """
    Web research specialist that retrieves real-time search results.

    Uses Brave Search via Locus Wrapped API — no upstream Brave account needed.
    Payment is deducted automatically from the Locus wallet (~$0.035/call).

    Parameters
    ----------
    api_key : str, optional
        Override for the LOCUS_API_KEY env var (useful in tests).
    result_count : int
        How many web results to request (1-20). Defaults to 5.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        result_count: int = _DEFAULT_COUNT,
    ) -> None:
        super().__init__(
            name="Search Agent",
            description="Searches the web for real-time information using Brave Search.",
            speciality="Web Research",
            rate_per_task=2.00,
            agent_id="search_agent_v1",
            developer="Team TS Xenkai",
            developer_wallet="0x7a67133e923c88748607d39a98ede9b2d660dac7"
        )
        self._api_key      = api_key or _LOCUS_API_KEY
        self._result_count = result_count

    # ------------------------------------------------------------------ #
    #  Core execution                                                       #
    # ------------------------------------------------------------------ #

    def execute(self, task: str) -> dict:
        """
        Search the web for the given query and return structured results.

        Parameters
        ----------
        task : str
            The search query / research question.

        Returns
        -------
        dict
            {
              "results": [
                {
                  "title":     str,
                  "url":       str,
                  "summary":   str,
                  "relevance": float   # 0.0-1.0, descending rank
                }
              ],
              "total_results": int,
              "query":         str
            }

        Raises
        ------
        RuntimeError
            If the Locus / Brave API returns a non-200 response.
        """
        if not self._api_key or self._api_key.startswith("claw_your"):
            return self._mock_results(task)

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type":  "application/json",
        }
        payload = {
            "q":     task,
            "count": self._result_count,
        }

        response = requests.post(_BRAVE_ENDPOINT, headers=headers, json=payload, timeout=30)

        if response.status_code != 200:
            if "Insufficient USDC balance" in response.text or response.status_code in (402, 403):
                print(f"⚠️ [SearchAgent] API blocked (Insufficient Balance). Falling back to MOCK data.")
                return self._mock_results(task)
            raise RuntimeError(
                f"Brave Search API error {response.status_code}: {response.text}"
            )

        data = response.json()
        raw_results = (
            data.get("data", {})
                .get("web", {})
                .get("results", [])
        )

        results = []
        total   = len(raw_results)
        for i, item in enumerate(raw_results):
            results.append({
                "title":     item.get("title", ""),
                "url":       item.get("url", ""),
                "summary":   item.get("description", ""),
                "relevance": round(1.0 - (i / max(total, 1)) * 0.5, 2),
            })

        return {
            "results":       results,
            "total_results": total,
            "query":         task,
        }

    # ------------------------------------------------------------------ #
    #  Mock fallback (no API key / testing)                                 #
    # ------------------------------------------------------------------ #

    def _mock_results(self, query: str) -> dict:
        """Return deterministic mock results when no real API key is set."""
        results = [
            {
                "title":     f"[MOCK] {query} — Market Overview 2024",
                "url":       "https://example.com/ev-india-overview",
                "summary":   f"Comprehensive overview of {query} including market size, key players, and growth projections.",
                "relevance": 1.0,
            },
            {
                "title":     f"[MOCK] {query} — Government Policy Update",
                "url":       "https://example.com/ev-india-policy",
                "summary":   f"Latest government initiatives and subsidies driving {query} adoption.",
                "relevance": 0.85,
            },
            {
                "title":     f"[MOCK] {query} — Consumer Trends",
                "url":       "https://example.com/ev-india-consumers",
                "summary":   f"Consumer sentiment and purchasing trends for {query} in 2024.",
                "relevance": 0.70,
            },
        ]
        return {
            "results":       results,
            "total_results": len(results),
            "query":         query,
        }
