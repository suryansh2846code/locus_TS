import time
from config import LOCUS_API_KEY
from .locus_payments import get_balance, pay_agent
from .agent_registry import AgentRegistry

# Placeholder imports for specialist agents (Phase 3 connection)
# For now, we use a simple generic mock for verification
try:
    from agents.search_agent import SearchAgent
    from agents.analysis_agent import AnalysisAgent
    from agents.writing_agent import WritingAgent
except ImportError:
    # Fallback to base or mock if not yet fully implemented by partner
    class MockAgent:
        def __init__(self, name, wallet_address, price): self.name = name
        def execute_task(self, data): return f"Mock results from {self.name} for: {data}"
    SearchAgent = MockAgent
    AnalysisAgent = MockAgent
    WritingAgent = MockAgent

SEARCH_ADDR = "0x1111111111111111111111111111111111111111"
ANALYSIS_ADDR = "0x2222222222222222222222222222222222222222"
WRITING_ADDR = "0x3333333333333333333333333333333333333333"

class ManagerAgent:
    def __init__(self):
        self.api_key = LOCUS_API_KEY
        self.registry = AgentRegistry()
        self.jobs_completed = 0
        
        # Register specialist agents with placeholder addresses
        self.registry.register_agent("SearchAgent", ["search"], SEARCH_ADDR, 0.0)
        self.registry.register_agent("AnalysisAgent", ["analysis"], ANALYSIS_ADDR, 0.0)
        self.registry.register_agent("WritingAgent", ["writing"], WRITING_ADDR, 0.0)
        
        # Instantiate agents for execution
        # We pass dummy values that match the registered ones
        self.search_agent = SearchAgent("SearchAgent", SEARCH_ADDR, 0.0)
        self.analysis_agent = AnalysisAgent("AnalysisAgent", ANALYSIS_ADDR, 0.0)
        self.writing_agent = WritingAgent("WritingAgent", WRITING_ADDR, 0.0)
        
        print("AgentMarket Manager Ready ✅")

    def calculate_splits(self, budget: float) -> dict:
        """Calculates 20/20/20/40 budget splits."""
        return {
            "search": round(budget * 0.20, 2),
            "analysis": round(budget * 0.20, 2),
            "writing": round(budget * 0.20, 2),
            "platform": round(budget * 0.40, 2)
        }

    def process_request(self, query: str, budget: float):
        """
        Main orchestration function.
        Yields progress updates and executes the full pipeline.
        """
        start_time = time.time()
        payment_records = []
        
        print(f"\n🚀 New Request Received: '{query}' | Budget: ${budget}")
        
        # Step 1: Calculate splits
        splits = self.calculate_splits(budget)
        
        # Step 2: Search
        print("🔍 Search Agent starting...")
        search_results = self.search_agent.execute_task(query) or f"Results for {query}"
        print(f"💸 Paying Search Agent ${splits['search']}...")
        tx_id = pay_agent(SEARCH_ADDR, splits['search'], "SearchAgent", "Web Search")
        payment_records.append({"agent": "SearchAgent", "tx_id": tx_id, "amount": splits['search']})
        yield {"step": "search_complete", "paid": splits["search"], "tx_id": tx_id}
        
        # Step 3: Analysis
        print("📊 Analysis Agent starting...")
        analysis_results = self.analysis_agent.execute_task(search_results) or f"Analysis of {search_results}"
        print(f"💸 Paying Analysis Agent ${splits['analysis']}...")
        tx_id = pay_agent(ANALYSIS_ADDR, splits['analysis'], "AnalysisAgent", "Data Analysis")
        payment_records.append({"agent": "AnalysisAgent", "tx_id": tx_id, "amount": splits['analysis']})
        yield {"step": "analysis_complete", "paid": splits["analysis"], "tx_id": tx_id}
        
        # Step 4: Writing
        print("📝 Writing Agent starting...")
        final_report = self.writing_agent.execute_task(analysis_results) or f"Final Report on {analysis_results}"
        print(f"💸 Paying Writing Agent ${splits['writing']}...")
        tx_id = pay_agent(WRITING_ADDR, splits['writing'], "WritingAgent", "Report Generation")
        payment_records.append({"agent": "WritingAgent", "tx_id": tx_id, "amount": splits['writing']})
        yield {"step": "writing_complete", "paid": splits["writing"], "tx_id": tx_id}
        
        # Step 5: Finalize
        self.jobs_completed += 1
        end_time = time.time()
        
        result = {
            "success": True,
            "query": query,
            "report": final_report,
            "transactions": payment_records,
            "total_cost": budget,
            "platform_profit": splits["platform"],
            "time_taken": round(end_time - start_time, 2)
        }
        
        print(f"✅ Job Complete! Profit: ${splits['platform']}")
        yield {"step": "complete", "result": result}

    def get_status(self) -> dict:
        """Returns marketplace health status."""
        balance = get_balance()
        return {
            "wallet_balance": balance,
            "agents_registered": len(self.registry.get_all_agents()),
            "total_jobs_done": self.jobs_completed
        }
