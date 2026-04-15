"""
agents/image_prompt_agent.py
?????????????????????????
Specialist agent that reverse engineers requests into detailed image generation prompts using Claude via the Locus Wrapped Anthropic API.
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
_MAX_TOKENS          = 1000

_SYSTEM_PROMPT = """You are a master image generation prompt engineer.
Return ONLY valid JSON in this exact format:
{
  "prompt": "Highly detailed, comma-separated midjourney-style image prompt",
  "negative_prompt": "Things to avoid in the generation",
  "style_tags": ["tag1", "tag2"],
  "recommended_model": "Model name (e.g., Midjourney v6, Stable Diffusion 3, DALL-E 3)"
}"""


class ImagePromptAgent(BaseAgent):
    def __init__(self, api_key: Optional[str] = None) -> None:
        super().__init__(
            name="Image Prompt Agent",
            description="Generates rich prompts for visual content and art.",
            speciality="Image Generation",
            rate_per_task=1.50,
            agent_id="image_prompt_agent_v1",
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
                    "content": f"Create an optimal image generation prompt for this request:\n\n{task}",
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
            "prompt": "Failed to parse JSON response. Raw output preserved.",
            "negative_prompt": "",
            "style_tags": [],
            "recommended_model": raw[:500]
        }

    def _mock_analysis(self, task: str) -> dict:
        return {
            "prompt": "[MOCK] A beautiful sunset over a cyberpunk city, neon lights, highly detailed, 8k resolution, cinematic lighting",
            "negative_prompt": "[MOCK] text, watermark, bad anatomy, blurry",
            "style_tags": ["cyberpunk", "cinematic", "neon"],
            "recommended_model": "Midjourney v6"
        }
