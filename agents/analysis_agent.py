"""
agents/analysis_agent.py
─────────────────────────
Specialist agent that analyses raw text / search results and extracts
structured insights using Claude via the Locus Wrapped Anthropic API.

Locus endpoint used:
  POST https://beta-api.paywithlocus.com/api/wrapped/anthropic/chat
  Model: claude-haiku-4-5  (fast + cost-efficient)
  Estimated cost: ~$0.001–$0.05 per call

Docs: https://beta.paywithlocus.com/wapi/anthropic.md
"""

from __future__ import annotations

import json
import os
import re
import sys
import requests
from typing import Optional
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent

load_dotenv()

# ── Locus API config ────────────────────────────────────────────────────────
_LOCUS_API_KEY       = os.getenv("LOCUS_API_KEY", "")
_ANTHROPIC_ENDPOINT  = "https://beta-api.paywithlocus.com/api/wrapped/anthropic/chat"
_MODEL               = "claude-haiku-4-5"
_MAX_TOKENS          = 1500

_SYSTEM_PROMPT = """You are a senior data analyst. Given research content, extract:
1. Key findings (factual statements)
2. Trends (directional changes or patterns)
3. Important numbers (statistics, figures, percentages)
4. A concise summary

Return ONLY valid JSON in this exact format:
{
  "key_findings": ["finding 1", "finding 2", ...],
  "trends": ["trend 1", "trend 2", ...],
  "important_numbers": ["stat 1", "stat 2", ...],
  "summary": "2-3 sentence executive summary"
}"""


class AnalysisAgent(BaseAgent):
    """
    Data analysis specialist that extracts insights from raw research content.

    Uses Claude (claude-haiku-4-5) via Locus Wrapped Anthropic API.
    Payment is deducted automatically from the Locus wallet.

    Parameters
    ----------
    api_key : str, optional
        Override for the LOCUS_API_KEY env var (useful in tests).
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        super().__init__(
            name="Analysis Agent",
            description="Analyzes data and extracts key insights using Claude AI.",
            speciality="Data Analysis",
            rate_per_task=0.10,
            agent_id="analysis_agent_v1",
            developer="Team TS Xenkai",
            developer_wallet="0x7a67133e923c88748607d39a98ede9b2d660dac7"
        )
        self._api_key = api_key or _LOCUS_API_KEY

    # ------------------------------------------------------------------ #
    #  Core execution                                                       #
    # ------------------------------------------------------------------ #

    def execute(self, task: str) -> dict:
        """
        Analyse the provided research content and return structured insights.

        Parameters
        ----------
        task : str
            Raw text to analyse — typically stringified search results.

        Returns
        -------
        dict
            {
              "key_findings":       [str, ...],
              "trends":             [str, ...],
              "important_numbers":  [str, ...],
              "summary":            str
            }

        Raises
        ------
        RuntimeError
            If the Locus / Anthropic API returns a non-200 response.
        """
        if not self._api_key or self._api_key.startswith("claw_your"):
            return self._mock_analysis(task)

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type":  "application/json",
        }
        payload = {
            "model":      _MODEL,
            "max_tokens": _MAX_TOKENS,
            "system":     _SYSTEM_PROMPT,
            "messages": [
                {
                    "role":    "user",
                    "content": f"Analyse the following research content:\n\n{task}",
                }
            ],
        }

        response = requests.post(_ANTHROPIC_ENDPOINT, headers=headers, json=payload, timeout=60)

        if response.status_code != 200:
            if "Insufficient USDC balance" in response.text or response.status_code in (402, 403):
                print(f"⚠️ [AnalysisAgent] API blocked (Insufficient Balance). Falling back to MOCK insights.")
                return self._mock_analysis(task)
            raise RuntimeError(
                f"Anthropic API error {response.status_code}: {response.text}"
            )

        data        = response.json()
        raw_content = data.get("data", {}).get("content", [{}])[0].get("text", "")

        return self._parse_response(raw_content, task)

    # ------------------------------------------------------------------ #
    #  Response parsing                                                     #
    # ------------------------------------------------------------------ #

    def _parse_response(self, raw: str, original_task: str) -> dict:
        """Extract JSON from Claude's response, with fallback parsing."""
        # Try to parse JSON directly
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON block from markdown fences
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Last resort: return structured fallback with raw text preserved
        return {
            "key_findings":      [raw[:300]] if raw else ["No analysis available."],
            "trends":            ["Unable to parse trends from response."],
            "important_numbers": [],
            "summary":           raw[:500] if raw else "Analysis failed.",
        }

    # ------------------------------------------------------------------ #
    #  Mock fallback (no API key / testing)                                 #
    # ------------------------------------------------------------------ #

    def _mock_analysis(self, task: str) -> dict:
        """Return deterministic mock analysis when no real API key is set."""
        return {
            "key_findings": [
                "[MOCK] India's EV market grew 49% YoY in FY2024 reaching 1.67 million units.",
                "[MOCK] Two-wheelers dominate with 59% market share; four-wheelers at 5.9%.",
                "[MOCK] Tata Motors leads passenger EV segment with over 70% market share.",
                "[MOCK] Government FAME-II scheme disbursed ₹10,000 crore in subsidies.",
            ],
            "trends": [
                "[MOCK] Rapid infrastructure expansion: charging stations growing at 80% CAGR.",
                "[MOCK] Battery costs declining — projected to reach $100/kWh by 2026.",
                "[MOCK] Tier-2 cities emerging as next growth frontier.",
            ],
            "important_numbers": [
                "[MOCK] 1.67 million EV units sold in FY2024",
                "[MOCK] ₹10,000 crore total FAME-II subsidy disbursement",
                "[MOCK] 49% year-over-year market growth",
                "[MOCK] 70%+ market share held by Tata Motors in passenger EVs",
            ],
            "summary": (
                "[MOCK] India's electric vehicle sector is experiencing explosive growth, "
                "driven by government incentives and falling battery costs. "
                "Two-wheelers lead adoption while Tata Motors dominates the passenger segment. "
                "The market is poised for continued expansion as infrastructure scales."
            ),
        }
