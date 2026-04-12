import sys
import os
import json
from unittest.mock import patch, MagicMock

# Add the project root to sys.path
sys.path.append('/Users/suryanshsingh/workspace/locus_hackathon/agentmarket-locus')

from core.manager_agent import ManagerAgent

def test_protections():
    manager = ManagerAgent()
    
    print("\n--- Testing Budget Too Low (< 0.50) ---")
    gen = manager.process_request("test", 0.10)
    result = next(gen)
    print(f"Result: {result}")
    assert result["step"] == "error"
    assert result["result"]["error"] == "budget_too_low"
    
    print("\n--- Testing Budget Too High (> 20.00) ---")
    gen = manager.process_request("test", 50.00)
    result = next(gen)
    print(f"Result: {result}")
    assert result["step"] == "error"
    assert result["result"]["error"] == "budget_too_high"
    
    print("\n--- Testing Insufficient Balance ---")
    with patch('core.manager_agent.get_balance', return_value=1.00):
        gen = manager.process_request("test", 5.00)
        result = next(gen)
        print(f"Result: {result}")
        assert result["step"] == "error"
        assert result["result"]["error"] == "insufficient_balance"

    print("\n--- Testing Payment Failure Handling ---")
    # Mock pay_agent to return failure
    mock_fail = {"success": False, "tx_id": None, "error": "Payment failed - insufficient balance"}
    with patch('core.manager_agent.get_balance', return_value=100.00):
        with patch('core.manager_agent.pay_agent', return_value=mock_fail):
            updates = list(manager.process_request("test", 10.00))
            
            # Check if pipeline completed
            steps = [u["step"] for u in updates]
            print(f"Steps taken: {steps}")
            assert "done" in steps
            
            # Check final result for payment records
            done_step = next(u for u in updates if u["step"] == "done")
            payments = done_step["result"]["transactions"]
            print(f"Payments: {payments}")
            for p in payments:
                assert p["success"] is False
                assert p["tx_id"] is None
            
            print("✅ Payment failure gracefully handled!")

if __name__ == "__main__":
    test_protections()
