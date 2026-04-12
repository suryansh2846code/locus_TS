import sys
import os
import json
from unittest.mock import patch, MagicMock

# Add the project root to sys.path
sys.path.append('/Users/suryanshsingh/workspace/locus_hackathon/agentmarket-locus')

from core.manager_agent import ManagerAgent

def test_pay_before_work():
    manager = ManagerAgent()
    
    print("\n--- Testing Success Flow ---")
    mock_success = {"success": True, "tx_id": "0x123", "status": "completed"}
    with patch('core.manager_agent.get_balance', return_value=100.00):
        with patch('core.manager_agent.pay_agent', return_value=mock_success):
            with patch.object(manager.search_agent, 'execute', return_value="search results") as mock_search:
                updates = list(manager.process_request("test", 10.00))
                steps = [u["step"] for u in updates]
                print(f"Steps: {steps}")
                assert "done" in steps
                mock_search.assert_called_once()
                print("✅ Success flow passed!")

    print("\n--- Testing Payment Failure at Search Step ---")
    mock_fail = {"success": False, "tx_id": None, "error": "Allowance blocked"}
    with patch('core.manager_agent.get_balance', return_value=100.00):
        with patch('core.manager_agent.pay_agent', return_value=mock_fail):
            with patch.object(manager.search_agent, 'execute', return_value="search results") as mock_search:
                updates = list(manager.process_request("test", 10.00))
                
                # Check metrics
                error_step = next((u for u in updates if u["step"] == "error"), None)
                print(f"Error Step: {error_step}")
                
                assert error_step is not None
                assert error_step["result"]["error"] == "payment_failed"
                assert error_step["result"]["step_failed"] == "search_payment"
                
                # CRITICAL: Execute should NOT have been called
                mock_search.assert_not_called()
                print("✅ Payment failure protection passed! (Agent did not work for free)")

    print("\n--- Testing Partial Execution with Middle Step Failure ---")
    # First payment succeeds, second fails
    with patch('core.manager_agent.get_balance', return_value=100.00):
        with patch('core.manager_agent.pay_agent') as mock_pay:
            mock_pay.side_effect = [
                {"success": True, "tx_id": "0x1", "status": "completed"}, # search pay
                {"success": False, "tx_id": None, "error": "Allowance limit"}, # analysis pay
            ]
            with patch.object(manager.search_agent, 'execute', return_value="search results") as mock_search:
                with patch.object(manager.analysis_agent, 'execute', return_value="analysis results") as mock_analysis:
                    updates = list(manager.process_request("test", 10.00))
                    
                    steps = [u["step"] for u in updates]
                    print(f"Steps: {steps}")
                    
                    error_step = next((u for u in updates if u["step"] == "error"), None)
                    print(f"Error Step: {error_step}")
                    
                    assert error_step["result"]["step_failed"] == "analysis_payment"
                    mock_search.assert_called_once()
                    mock_analysis.assert_not_called()
                    print("✅ Partial execution protection passed!")

if __name__ == "__main__":
    test_pay_before_work()
