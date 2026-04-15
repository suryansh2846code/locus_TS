import sys
import os

# Add the project root to sys.path to allow imports from core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.manager_agent import ManagerAgent

def test_manager_flow():
    print("? Testing ManagerAgent Orchestration Flow...\n")
    
    # Init Manager
    manager = ManagerAgent()
    
    # Test Split Calculation
    budget = 10.0
    splits = manager.calculate_splits(budget)
    print(f"\n? Calculated Splits for ${budget}:")
    for key, val in splits.items():
        print(f"   - {key}: ${val}")
    
    # Test Workflow (processing query)
    query = "Researching AI safety in 2026"
    print(f"\n? Running Pipeline for: '{query}'")
    
    for progress in manager.process_request(query, budget):
        step = progress.get("step")
        if step == "search_complete":
            print(f"   [Internal] Search done. Paid: ${progress.get('paid')}")
        elif step == "analysis_complete":
            print(f"   [Internal] Analysis done. Paid: ${progress.get('paid')}")
        elif step == "writing_complete":
            print(f"   [Internal] Writing done. Paid: ${progress.get('paid')}")
        elif step == "complete":
            result = progress.get("result")
            print("\n? Pipeline Completed Successfully!")
            print(f"   - Time Taken: {result['time_taken']}s")
            print(f"   - Total Profit: ${result['platform_profit']}")
            print(f"   - Final Report Snippet: {result['report'][:50]}...")

    # Test Status
    print("\n? Marketplace Status:")
    status = manager.get_status()
    for key, val in status.items():
        print(f"   - {key}: {val}")

if __name__ == "__main__":
    test_manager_flow()
