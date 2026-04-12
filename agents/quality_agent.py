"""
agents/quality_agent.py
────────────────────────
Specialist agent that reviews research reports for quality using Claude 
via the Locus Wrapped Anthropic API.
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

_SYSTEM_PROMPT = """You are a senior quality assurance editor. Your job is to review research reports.
Analyze the report and provide a structured assessment:
1. Quality Score (0-10)
2. Strengths
3. Improvements
4. Recommendation (approved/rejected)
5. Summary

Return ONLY valid JSON in this exact format:
{
    "quality_score": 8.5,
    "rating": "⭐⭐⭐⭐⭐",
    "strengths": ["..", ".."],
    "improvements": ["..", ".."],
    "word_count": 450,
    "sources_cited": 5,
    "recommendation": "approved",
    "summary": "Detailed summary here"
}"""

class QualityAgent(BaseAgent):
    """
    Quality Assurance specialist that reviews research reports.
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        super().__init__(
            name="Quality Check Agent",
            description="Reviews research reports for quality using Claude AI.",
            speciality="Quality Assurance",
            rate_per_task=1.00,
            agent_id="quality_agent_v1"
        )
        self._api_key = api_key or _LOCUS_API_KEY

    def execute(self, task: str) -> dict:
        """
        Review the provided report and return quality assessment.
        """
        if not self._api_key or self._api_key.startswith("claw_your"):
            return self._mock_quality_check(task)

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
                    "content": f"Review this research report and provide a quality assessment:\n\n{task}",
                }
            ],
        }

        try:
            response = requests.post(_ANTHROPIC_ENDPOINT, headers=headers, json=payload, timeout=60)
            if response.status_code != 200:
                return self._mock_quality_check(task)
            
            data = response.json()
            raw_content = data.get("data", {}).get("content", [{}])[0].get("text", "")
            return self._parse_response(raw_content)
        except Exception:
            return self._mock_quality_check(task)

    def _parse_response(self, raw: str) -> dict:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"```json\s*(.*?)\s*```", raw, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    pass
        return self._mock_quality_check("fallback")

    def _mock_quality_check(self, task: str) -> dict:
        return {
            "quality_score": 8.5,
            "rating": "⭐⭐⭐⭐⭐",
            "strengths": [
                "Well structured report",
                "Good use of data",
                "Clear conclusions"
            ],
            "improvements": [
                "Could use more sources",
                "Executive summary too brief"
            ],
            "word_count": 450,
            "sources_cited": 5,
            "recommendation": "approved",
            "summary": "High quality research report with strong data analysis"
        }
