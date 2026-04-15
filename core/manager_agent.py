import os
import time
import json
import re
import requests
from datetime import datetime
from config import LOCUS_API_KEY
from .locus_payments import get_balance, pay_agent, SEARCH_AGENT_WALLET, ANALYSIS_AGENT_WALLET, WRITING_AGENT_WALLET
from .agent_registry import AgentRegistry, registry

class PaymentFailedError(Exception):
    """Raised when an agent payment fails."""
    def __init__(self, message, agent_name, amount, step_failed):
        super().__init__(message)
        self.agent_name = agent_name
        self.amount = amount
        self.step_failed = step_failed

# Specialist agents built by partner
try:
    from agents.search_agent import SearchAgent
    from agents.analysis_agent import AnalysisAgent
    from agents.writing_agent import WritingAgent
    from agents.quality_agent import QualityAgent
    from agents.code_agent import CodeAgent
    from agents.legal_agent import LegalAgent
    from agents.image_prompt_agent import ImagePromptAgent
    from agents.data_agent import DataAgent
    from agents.base_agent import BaseAgent
except ImportError:
    from agents.base_agent import BaseAgent
    class MockAgent(BaseAgent):
        def __init__(self, name="Mock", description="Mock", speciality="Mock", rate_per_task=0.0):
            super().__init__(name, description, speciality, rate_per_task)
        def execute(self, task): return f"Mock results from {self.name} for: {task}"
    SearchAgent = MockAgent
    AnalysisAgent = MockAgent
    WritingAgent = MockAgent
    QualityAgent = MockAgent
    CodeAgent = MockAgent
    LegalAgent = MockAgent
    ImagePromptAgent = MockAgent
    DataAgent = MockAgent

# Agent wallet addresses from environment
SEARCH_ADDR = SEARCH_AGENT_WALLET
ANALYSIS_ADDR = ANALYSIS_AGENT_WALLET
WRITING_ADDR = WRITING_AGENT_WALLET
PLATFORM_ADDR = "0x0b3743ca11a26c28c074dbdef4606c5991a29fc2"

_ANTHROPIC_ENDPOINT  = "https://beta-api.paywithlocus.com/api/wrapped/anthropic/chat"
_ROUTER_MODEL        = "claude-haiku-4-5"
_ROUTER_PROMPT       = """You are an agent router for AgentMarket. Given a user's service request, return a JSON array of agent IDs that should handle this task. Available agents: search_agent, analysis_agent, writing_agent, quality_agent, code_agent, legal_agent, image_prompt_agent, data_agent. Rules: always include quality_agent last. Only include agents relevant to the task. Return ONLY valid JSON array, no explanation."""

class ManagerAgent:
    def __init__(self):
        self.api_key = LOCUS_API_KEY
        self.registry = registry
        self.jobs_completed = 0
        
        # Load agent config
        config_path = os.path.join(os.path.dirname(__file__), '..', 'agents', 'agent_config.json')
        self.registry.load_from_config(config_path)
        
        # Instantiate agents for execution
        self.search_agent = SearchAgent()
        self.analysis_agent = AnalysisAgent()
        self.writing_agent = WritingAgent()
        self.quality_agent = QualityAgent()
        
        # New Dynamic Agents
        self.code_agent = CodeAgent()
        self.legal_agent = LegalAgent()
        self.image_prompt_agent = ImagePromptAgent()
        self.data_agent = DataAgent()

        # Assign addresses
        self.search_agent.wallet_address = SEARCH_ADDR
        self.analysis_agent.wallet_address = ANALYSIS_ADDR
        self.writing_agent.wallet_address = WRITING_ADDR
        self.quality_agent.wallet_address = "0x7a67133e923c88748607d39a98ede9b2d660dac7"
        
        # For new agents, just use a default valid destination wallet or platform addr for testing
        self.code_agent.wallet_address = "0x7a67133e923c88748607d39a98ede9b2d660dac7"
        self.legal_agent.wallet_address = "0x7a67133e923c88748607d39a98ede9b2d660dac7"
        self.image_prompt_agent.wallet_address = "0x7a67133e923c88748607d39a98ede9b2d660dac7"
        self.data_agent.wallet_address = "0x7a67133e923c88748607d39a98ede9b2d660dac7"
        
        # Mapping by ID for routing
        self.agent_map = {
            "search_agent": self.search_agent,
            "analysis_agent": self.analysis_agent,
            "writing_agent": self.writing_agent,
            "quality_agent": self.quality_agent,
            "code_agent": self.code_agent,
            "legal_agent": self.legal_agent,
            "image_prompt_agent": self.image_prompt_agent,
            "data_agent": self.data_agent
        }

        # Register specialist agents with the global registry
        for agent in self.agent_map.values():
            self.registry.register_agent(agent)
            
        print("AgentMarket Manager Ready ✅")

    def _save_job_history(self, job_data: dict) -> None:
        """Appends a completed job to the history file."""
        history_path = "jobs.json"
        history = {"jobs": []}
        
        if os.path.exists(history_path):
            with open(history_path, "r") as f:
                try:
                    history = json.load(f)
                except:
                    pass
        
        history["jobs"].insert(0, job_data)
        history["jobs"] = history["jobs"][:50]
        
        with open(history_path, "w") as f:
            json.dump(history, f, indent=2)

    def update_agent_stats(self, agent_results: list[dict]) -> None:
        """Flushes agent performance results to the registry."""
        for res in agent_results:
            self.registry.update_agent_after_job(
                agent_name=res["name"],
                success=res.get("success", True),
                amount_earned=res.get("amount", 0.0)
            )

    def select_agents(self, query: str) -> list[str]:
        """Calls Claude Haiku to dynamically route the query to specific agents."""
        if not self.api_key or self.api_key.startswith("claw_your"):
            # Mock dynamic fallback
            if "code" in query.lower() or "script" in query.lower():
                return ["code_agent", "quality_agent"]
            return ["search_agent", "analysis_agent", "writing_agent", "quality_agent"]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type":  "application/json",
        }
        payload = {
            "model":      _ROUTER_MODEL,
            "max_tokens": 500,
            "system":     _ROUTER_PROMPT,
            "messages": [{"role": "user", "content": f"Select agents for this request: {query}"}]
        }
        
        try:
            response = requests.post(_ANTHROPIC_ENDPOINT, headers=headers, json=payload, timeout=20)
            if response.status_code == 200:
                raw = response.json().get("data", {}).get("content", [{}])[0].get("text", "")
                
                # Try to parse JSON array
                try:
                    agents = json.loads(raw)
                    if isinstance(agents, list):
                        return [a for a in agents if a in self.agent_map]
                except json.JSONDecodeError:
                    match = re.search(r"\[.*?\]", raw, re.DOTALL)
                    if match:
                        agents = json.loads(match.group(0))
                        return [a for a in agents if a in self.agent_map]
        except Exception as e:
            print(f"Error in select_agents: {e}")
            
        print("Fallback dynamic agent routing used.")
        return ["search_agent", "analysis_agent", "writing_agent", "quality_agent"]

    def calculate_splits_dynamic(self, budget: float, selected_agent_ids: list[str]) -> dict:
        """Calculates budget splits based on dynamically selected agents."""
        agent_costs = {}
        total_agent_cost = 0.0
        
        for a_id in selected_agent_ids:
            agent = self.agent_map[a_id]
            # Use registry to get dynamic rate if user updated it
            rate = self.registry.get_agent_rate(agent.name)
            agent_costs[a_id] = rate
            total_agent_cost += rate
            
        platform_fee = budget - total_agent_cost
        
        if platform_fee < 0:
            return {
                "valid": False,
                "error": f"Budget too low! Minimum needed: ${total_agent_cost + 0.50}"
            }
            
        return {
            "valid": True,
            "costs": agent_costs,
            "platform": round(platform_fee, 2),
            "total_agent_cost": total_agent_cost
        }

    def pay_and_execute(self, agent, task, amount, step_name):
        """Pays the agent first, then executes the task only if payment succeeds."""
        # Clean memo to 100 chars
        clean_task_memo = str(task)[:100]
        
        # Pay FIRST
        payment = pay_agent(
            agent.wallet_address, 
            amount, 
            agent.name, 
            clean_task_memo
        )
        
        if not payment["success"]:
            raise PaymentFailedError(
                message=f"Could not pay {agent.name}. Please check your Locus allowance settings.",
                agent_name=agent.name,
                amount=amount,
                step_failed=step_name
            )
        
        print(f"💰 Payment for {agent.name} confirmed. Proceeding with execution...")
        result = agent.execute(task)
        return result, payment

    def process_request(self, query: str, budget: float):
        """Orchestrates the dynamic agent pipeline."""
        start_time = time.time()
        
        if budget < 0.50:
            yield {"step": "error", "error": "budget_too_low", "message": "Minimum budget is $0.50", "result": {"success": False, "error": "budget_too_low"}}
            return

        if budget > 20.00:
            yield {"step": "error", "error": "budget_too_high", "message": "Maximum budget is $20.00", "result": {"success": False, "error": "budget_too_high"}}
            return

        current_balance = get_balance()
        if budget > current_balance:
            yield {"step": "error", "error": "insufficient_balance", "message": f"Budget ${budget} exceeds wallet balance ${current_balance}", "result": {"success": False, "error": "insufficient_balance", "current_balance": current_balance}}
            return

        # Phase 1: Dynamic Agent Routing
        yield {"step": "manager_started", "query": query, "budget": budget}
        print("🧠 Selecting agents dynamically...")
        selected_agent_ids = self.select_agents(query)
        
        # Ensure quality agent is at the end
        if "quality_agent" in selected_agent_ids:
            selected_agent_ids.remove("quality_agent")
        selected_agent_ids.append("quality_agent")
        
        # Emit agents_selected SSE event
        yield {"step": "agents_selected", "agents": selected_agent_ids}
        
        splits = self.calculate_splits_dynamic(budget, selected_agent_ids)
        if not splits.get("valid", True):
            yield {"step": "error", "error": "insufficient_budget", "message": splits.get("error", "Budget too low for selected agents."), "result": {"success": False, "error": "insufficient_budget"}}
            return

        agent_performance = []
        payment_records = []
        
        try:
            import sys
            
            # Store workflow state to pass between agents
            context = f"Original Query: {query}\n"
            final_report = ""
            quality_score = 0
            quality_results = None
            
            for agent_id in selected_agent_ids:
                agent = self.agent_map[agent_id]
                cost = splits["costs"][agent_id]
                
                time.sleep(2) # Min Pacing
                yield {"step": f"{agent_id}_started"}
                sys.stdout.flush()
                print(f"🚀 Paying then Executing {agent.name} for context...")
                
                # Execution
                result_data, pay_result = self.pay_and_execute(
                    agent, 
                    context, 
                    cost,
                    f"{agent_id}_payment"
                )
                
                # Append to context for next agent
                result_str = json.dumps(result_data) if isinstance(result_data, dict) else str(result_data)
                context += f"\n--- {agent.name} Output ---\n{result_str}\n"
                
                # Save special states depending on the agent
                if agent_id == "quality_agent":
                    quality_results = result_data
                    if isinstance(quality_results, dict):
                        quality_score = quality_results.get("quality_score", 0)
                    final_report += f"\n\n---\n✅ Quality Score: {quality_score}/10"
                else:
                    final_report += f"\n\n### {agent.name} Results\n```json\n{result_str}\n```"

                # Record stats
                payment_records.append({
                    "agent": agent.name, 
                    "tx_id": pay_result.get("tx_id"), 
                    "amount": cost,
                    "success": True
                })
                agent_performance.append({"name": agent.name, "success": True, "amount": cost})
                yield {"step": f"{agent_id}_complete", "paid": cost, "tx_id": pay_result.get("tx_id"), "score": quality_score if agent_id == "quality_agent" else None}
            
            # Platform Fee Collection
            time.sleep(2)
            platform_fee = splits.get("platform", 0)
            sys.stdout.flush()
            if platform_fee > 0:
                print(f"🎖️ Collecting platform fee: ${platform_fee}")
                platform_pay = pay_agent(PLATFORM_ADDR, platform_fee, "Platform", f"Fee for request")
                if platform_pay["success"]:
                    payment_records.append({
                        "agent": "Platform",
                        "tx_id": platform_pay.get("tx_id"),
                        "amount": platform_fee,
                        "success": True
                    })
            
            elapsed = round(time.time() - start_time, 2)
            self.jobs_completed += 1
            
            # Persist stats and history
            self.update_agent_stats(agent_performance)
            
            job_history_entry = {
                "id": f"job_{int(time.time())}",
                "query": query,
                "budget": budget,
                "agents_used": [self.agent_map[a].name for a in selected_agent_ids],
                "time_taken": f"{elapsed}s",
                "status": "completed",
                "quality_score": quality_score,
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            }
            self._save_job_history(job_history_entry)
            
            final_result = {
                "success": True,
                "query": query,
                "report": final_report,
                "agents_used": selected_agent_ids,
                "quality": quality_results,
                "transactions": payment_records,
                "total_cost": budget,
                "platform_profit": splits["platform"],
                "time_taken": f"{elapsed}s"
            }
            
            yield {"step": "done", "report": final_report, "result": final_result}

        except PaymentFailedError as e:
            yield {
                "step": "error",
                "error": "payment_failed",
                "message": str(e),
                "result": {
                    "success": False,
                    "error": "payment_failed",
                    "step_failed": e.step_failed,
                    "amount_attempted": e.amount
                }
            }
            return
        except Exception as e:
            print(f"❌ Pipeline CRITICAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            yield {
                "step": "error",
                "error": "pipeline_crash",
                "message": f"Pipeline crashed: {str(e)}",
                "result": {
                    "success": False,
                    "error": str(e)
                }
            }
            return

    def get_status(self) -> dict:
        """Returns marketplace health status."""
        stats = self.registry.get_marketplace_stats()
        stats["wallet_balance"] = get_balance()
        stats["total_jobs_done"] = self.jobs_completed
        return stats
