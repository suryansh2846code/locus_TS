"""
agents/legal_agent.py
?????????????????????????
Specialist agent that analyzes and generates legal documents using Claude via the Locus Wrapped Anthropic API.
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

_LOCUS_API_KEY       = os.getenv("LOCUS_API_KEY", "")
_ANTHROPIC_ENDPOINT  = "https://beta-api.paywithlocus.com/api/wrapped/anthropic/chat"
_MODEL               = "claude-haiku-4-5"
_MAX_TOKENS          = 2000

_SYSTEM_PROMPT = """You are a senior legal counsel. Given a legal prompt, document, or task, provide professional analysis.
Return ONLY valid JSON in this exact format:
{
  "summary": "High-level summary of the legal document or advice",
  "key_clauses": ["Clause 1", "Clause 2"],
  "risks": ["Risk 1", "Risk 2"],
  "disclaimer": "Standard legal disclaimer stating this is AI advice and not formal legal representation"
}"""


class LegalAgent(BaseAgent):
    def __init__(self, api_key: Optional[str] = None) -> None:
        super().__init__(
            name="Legal Agent",
            description="Analyzes contracts, legal logic, terms of service, and compliance.",
            speciality="Law",
            rate_per_task=3.00,
            agent_id="legal_agent_v1",
            developer="Team TS Xenkai",
            developer_wallet="0x7a67133e923c88748607d39a98ede9b2d660dac7"
        )
        self._api_key = api_key or _LOCUS_API_KEY

    def execute(self, task: str) -> dict:
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
                    "content": f"Analyze this legal request:\n\n{task}",
                }
            ],
        }

        response = requests.post(_ANTHROPIC_ENDPOINT, headers=headers, json=payload, timeout=60)

        if response.status_code != 200:
            if "Insufficient USDC balance" in response.text or response.status_code in (402, 403):
                return self._mock_analysis(task)
            raise RuntimeError(f"Anthropic API error {response.status_code}: {response.text}")

        data = response.json()
        raw_content = data.get("data", {}).get("content", [{}])[0].get("text", "")

        return self._parse_response(raw_content, task)

    def _parse_response(self, raw: str, original_task: str) -> dict:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        return {
            "summary": "Failed to parse JSON response. Raw output preserved.",
            "key_clauses": [],
            "risks": ["Could not parse valid risks"],
            "disclaimer": raw[:500]
        }

    def _mock_analysis(self, task: str) -> dict:
        return {
            "summary": "[MOCK] Standard Non-Disclosure Agreement",
            "key_clauses": ["[MOCK] Confidential Obligations", "[MOCK] Exclusions", "[MOCK] Term of 3 Years"],
            "risks": ["[MOCK] Definition of confidential information is too broad"],
            "disclaimer": "This is a mock AI response, not professional legal counsel."
        }
