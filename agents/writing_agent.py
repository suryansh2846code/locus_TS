"""
agents/writing_agent.py
────────────────────────
Specialist agent that converts structured analysis into a professional
markdown research report using Claude via the Locus Wrapped Anthropic API.

Locus endpoint used:
  POST https://beta-api.paywithlocus.com/api/wrapped/anthropic/chat
  Model: claude-haiku-4-5
  Estimated cost: ~$0.001–$0.10 per call

Docs: https://beta.paywithlocus.com/wapi/anthropic.md
"""

from __future__ import annotations

import os
import sys
import requests
from typing import Optional
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent

load_dotenv()

# ── Locus API config ────────────────────────────────────────────────────────
_LOCUS_API_KEY      = os.getenv("LOCUS_API_KEY", "")
_ANTHROPIC_ENDPOINT = "https://beta-api.paywithlocus.com/api/wrapped/anthropic/chat"
_MODEL              = "claude-haiku-4-5"
_MAX_TOKENS         = 2000

_SYSTEM_PROMPT = """You are a professional research report writer.
Write in clear, authoritative, business-appropriate language.
Use markdown formatting. Structure every report with exactly these sections:
## Executive Summary
## Key Findings
## Market Data & Numbers
## Trends
## Conclusion

Be specific — use the data provided. Write in full paragraphs (not just bullets).
The report should read like a professional analyst brief."""


class WritingAgent(BaseAgent):
    """
    Report writing specialist that produces polished markdown research reports.

    Uses Claude (claude-haiku-4-5) via Locus Wrapped Anthropic API.
    Payment is deducted automatically from the Locus wallet.

    Parameters
    ----------
    api_key : str, optional
        Override for the LOCUS_API_KEY env var (useful in tests).
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        super().__init__(
            name="Writing Agent",
            description="Writes professional research reports from analysis insights.",
            speciality="Report Writing",
            rate_per_task=2.00,
            agent_id="writing_agent_v1",
            developer="Team TS Xenkai",
            developer_wallet="0x7a67133e923c88748607d39a98ede9b2d660dac7"
        )
        self._api_key = api_key or _LOCUS_API_KEY

    # ------------------------------------------------------------------ #
    #  Core execution                                                       #
    # ------------------------------------------------------------------ #

    def execute(self, task: str) -> str:
        """
        Transform analysis insights into a complete markdown research report.

        Parameters
        ----------
        task : str
            Stringified analysis data (output of AnalysisAgent, or any text).

        Returns
        -------
        str
            A complete markdown report with:
              ## Executive Summary
              ## Key Findings
              ## Market Data & Numbers
              ## Trends
              ## Conclusion

        Raises
        ------
        RuntimeError
            If the Locus / Anthropic API returns a non-200 response.
        """
        if not self._api_key or self._api_key.startswith("claw_your"):
            return self._mock_report(task)

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
                    "content": (
                        "Write a professional research report using the following analysis data. "
                        "Include all five required sections.\n\n"
                        f"Analysis data:\n{task}"
                    ),
                }
            ],
        }

        response = requests.post(_ANTHROPIC_ENDPOINT, headers=headers, json=payload, timeout=60)

        if response.status_code != 200:
            if "Insufficient USDC balance" in response.text or response.status_code in (402, 403):
                print(f"⚠️ [WritingAgent] API blocked (Insufficient Balance). Falling back to MOCK report.")
                return self._mock_report(task)
            raise RuntimeError(
                f"Anthropic API error {response.status_code}: {response.text}"
            )

        data        = response.json()
        report_text = data.get("data", {}).get("content", [{}])[0].get("text", "")

        if not report_text:
            raise RuntimeError("Writing Agent received an empty response from Claude.")

        return report_text

    # ------------------------------------------------------------------ #
    #  Mock fallback (no API key / testing)                                 #
    # ------------------------------------------------------------------ #

    def _mock_report(self, task: str) -> str:
        """Return a deterministic mock report when no real API key is set."""
        return """# Electric Vehicles in India — Research Report
*Generated by AgentMarket Writing Agent*

---

## Executive Summary

India's electric vehicle market is undergoing a transformative shift, emerging as one of the
fastest-growing EV markets globally. Driven by ambitious government policy, falling battery
costs, and rising fuel prices, the sector recorded 1.67 million unit sales in FY2024 —
a remarkable 49% year-over-year increase. This report synthesises the latest market data,
consumer trends, and policy developments to provide a comprehensive outlook for stakeholders.

---

## Key Findings

India's EV ecosystem has matured significantly over the past two years. Tata Motors has
consolidated its leadership in the passenger vehicle segment, commanding over 70% market
share with its Nexon EV and Tiago EV platforms. The two-wheeler segment, led by Ola Electric
and Ather Energy, accounts for 59% of total EV sales — reflecting the affordability-driven
nature of Indian consumer preferences.

Government support has been decisive. The FAME-II scheme disbursed ₹10,000 crore in
subsidies, significantly lowering the total cost of ownership for buyers and enabling OEMs
to offer competitive sticker prices. State-level incentives in Maharashtra, Gujarat, and
Delhi have further catalysed adoption.

---

## Market Data & Numbers

| Metric | Value |
|--------|-------|
| Total EV units sold (FY2024) | **1.67 million** |
| Year-over-year growth | **49%** |
| Two-wheeler market share | **59%** |
| Tata Motors passenger EV share | **70%+** |
| FAME-II subsidy disbursed | **₹10,000 crore** |
| Projected battery cost target | **$100/kWh by 2026** |
| Charging station CAGR | **80%** |

---

## Trends

**Infrastructure Acceleration:** India's public charging network is expanding at an 80% CAGR,
with a focus on highway corridors and urban parking hubs. Private charging solutions are
proliferating in residential complexes, reducing range anxiety for urban buyers.

**Battery Cost Deflation:** Domestic cell manufacturing initiatives under the PLI scheme are
on track to reduce battery pack costs to $100/kWh by 2026 — a threshold widely regarded
as the tipping point for EV-ICE price parity.

**Tier-2 City Penetration:** Early adopters were concentrated in metros. The next growth wave
is being driven by cities like Pune, Ahmedabad, Jaipur, and Lucknow, where two-wheelers
dominate commutes and payback periods are shorter.

---

## Conclusion

India's EV transition is no longer a future prospect — it is actively underway. The convergence
of policy support, technology cost reduction, and expanding infrastructure positions India
for continued hypergrowth through the decade. Stakeholders who act decisively in the next
24 months — whether through manufacturing investment, fleet electrification, or charging
infrastructure deployment — stand to capture disproportionate value in what will be one of
the world's most consequential mobility markets.

*[MOCK REPORT — generated without Locus API key]*
"""
