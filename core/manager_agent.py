import time
import json
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
    from agents.base_agent import BaseAgent
except ImportError:
    # Fallback to base or mock if not yet fully implemented by partner
    from agents.base_agent import BaseAgent
    class MockAgent(BaseAgent):
        def __init__(self, name="Mock", description="Mock", speciality="Mock", rate_per_task=0.0):
            super().__init__(name, description, speciality, rate_per_task)
        def execute(self, task): return f"Mock results from {self.name} for: {task}"
    SearchAgent = MockAgent
    AnalysisAgent = MockAgent
    WritingAgent = MockAgent

# Agent wallet addresses from environment
SEARCH_ADDR = SEARCH_AGENT_WALLET
ANALYSIS_ADDR = ANALYSIS_AGENT_WALLET
WRITING_ADDR = WRITING_AGENT_WALLET

class ManagerAgent:
    def __init__(self):
        self.api_key = LOCUS_API_KEY
        self.registry = registry
        self.jobs_completed = 0
        
        # Instantiate agents for execution
        self.search_agent = SearchAgent()
        self.analysis_agent = AnalysisAgent()
        self.writing_agent = WritingAgent()

        # Assign addresses
        self.search_agent.wallet_address = SEARCH_ADDR
        self.analysis_agent.wallet_address = ANALYSIS_ADDR
        self.writing_agent.wallet_address = WRITING_ADDR
        
        # Register specialist agents with the global registry
        self.registry.register_agent(self.search_agent)
        self.registry.register_agent(self.analysis_agent)
        self.registry.register_agent(self.writing_agent)
        
        print("AgentMarket Manager Ready ✅")

    def calculate_splits(self, budget: float) -> dict:
        """Calculates 20/20/20/40 budget splits."""
        return {
            "search": round(budget * 0.20, 2),
            "analysis": round(budget * 0.20, 2),
            "writing": round(budget * 0.20, 2),
            "platform": round(budget * 0.40, 2)
        }

    def pay_and_execute(self, agent, task, amount, step_name):
        """Pays the agent first, then executes the task only if payment succeeds."""
        # Pay FIRST
        payment = pay_agent(
            agent.wallet_address, 
            amount, 
            agent.name, 
            task
        )
        
        # Check payment succeeded
        if not payment["success"]:
            raise PaymentFailedError(
                message=f"Could not pay {agent.name}. Please check your Locus allowance settings.",
                agent_name=agent.name,
                amount=amount,
                step_failed=step_name
            )
        
        # ONLY execute after confirmed payment
        print(f"💰 Payment for {agent.name} confirmed. Proceeding with execution...")
        result = agent.execute(task)
        return result, payment

    def process_request(self, query: str, budget: float):
        """Orchestrates the agent pipeline: Search -> Analysis -> Writing."""
        start_time = time.time()
        
        # PROTECTION 2 — Minimum budget check
        if budget < 0.50:
            yield {
                "step": "error",
                "result": {
                    "success": False,
                    "error": "budget_too_low",
                    "message": "Minimum budget is $0.50"
                }
            }
            return

        # PROTECTION 3 — Maximum budget check
        if budget > 20.00:
            yield {
                "step": "error",
                "result": {
                    "success": False,
                    "error": "budget_too_high",
                    "message": "Maximum budget is $20.00"
                }
            }
            return

        # PROTECTION 1 — Check balance before starting
        current_balance = get_balance()
        if budget > current_balance:
            yield {
                "step": "error",
                "result": {
                    "success": False,
                    "error": "insufficient_balance",
                    "message": f"Budget ${budget} exceeds wallet balance ${current_balance}",
                    "current_balance": current_balance
                }
            }
            return

        splits = self.calculate_splits(budget)
        payment_records = []
        
        yield {"step": "manager_started", "query": query, "budget": budget}
        
        try:
            # 1. Search Agent
            yield {"step": "search_started"}
            print(f"🔍 Paying then Executing Search for: {query}")
            
            search_results, pay_result = self.pay_and_execute(
                self.search_agent, 
                "Web Search", 
                splits['search'],
                "search_payment"
            )
            
            search_str = json.dumps(search_results) if isinstance(search_results, dict) else str(search_results)
            payment_records.append({
                "agent": "SearchAgent", 
                "tx_id": pay_result.get("tx_id"), 
                "amount": splits['search'],
                "success": True
            })
            yield {"step": "search_complete", "paid": splits["search"], "tx_id": pay_result.get("tx_id")}
            
            # 2. Analysis Agent
            yield {"step": "analysis_started"}
            print("📊 Paying then Analyzing search patterns...")
            
            analysis_data, pay_result = self.pay_and_execute(
                self.analysis_agent, 
                "Data Analysis", 
                splits['analysis'],
                "analysis_payment"
            )
            
            analysis_str = json.dumps(analysis_data) if isinstance(analysis_data, dict) else str(analysis_data)
            payment_records.append({
                "agent": "AnalysisAgent", 
                "tx_id": pay_result.get("tx_id"), 
                "amount": splits['analysis'],
                "success": True
            })
            yield {"step": "analysis_complete", "paid": splits["analysis"], "tx_id": pay_result.get("tx_id")}
            
            # 3. Writing Agent
            yield {"step": "writing_started"}
            print("📝 Paying then Drafting final report...")
            
            report_md, pay_result = self.pay_and_execute(
                self.writing_agent, 
                "Report Generation", 
                splits['writing'],
                "writing_payment"
            )
            
            payment_records.append({
                "agent": "WritingAgent", 
                "tx_id": pay_result.get("tx_id"), 
                "amount": splits['writing'],
                "success": True
            })
            yield {"step": "writing_complete", "paid": splits["writing"], "tx_id": pay_result.get("tx_id")}
            
            elapsed = round(time.time() - start_time, 2)
            self.jobs_completed += 1
            
            final_result = {
                "success": True,
                "query": query,
                "report": report_md,
                "transactions": payment_records,
                "total_cost": budget,
                "platform_profit": splits["platform"],
                "time_taken": f"{elapsed}s"
            }
            
            yield {"step": "done", "report": report_md, "result": final_result}

        except PaymentFailedError as e:
            yield {
                "step": "error",
                "result": {
                    "success": False,
                    "error": "payment_failed",
                    "message": str(e),
                    "step_failed": e.step_failed,
                    "amount_attempted": e.amount
                }
            }
            return

    def get_status(self) -> dict:
        """Returns marketplace health status."""
        stats = self.registry.get_marketplace_stats()
        stats["wallet_balance"] = get_balance()
        stats["total_jobs_done"] = self.jobs_completed
        return stats
