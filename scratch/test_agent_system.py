import sys
import os
import json
import requests
from unittest.mock import patch, MagicMock

# Add the project root to sys.path
sys.path.append('/Users/suryanshsingh/workspace/locus_hackathon/agentmarket-locus')

from core.manager_agent import ManagerAgent
from api.app import app

def test_registration_system():
    manager = ManagerAgent()
    
    print("\n--- Testing Registry Loading ---")
    assert "Search Agent" in manager.registry.agents
    agent = manager.registry.agents["Search Agent"]
    # Check if it's an instance or dict
    agent_id = agent.id if hasattr(agent, "id") else agent["id"]
    assert agent_id == "search_agent_v1"
    print("✅ Registry loaded correctly from JSON")
    
    print("\n--- Testing Split Calculation ---")
    # Total agent cost = 2+2+2+1 = 7.0
    # Minimum budget needed = 7.0 + 0.5 = 7.5
    splits = manager.calculate_splits(10.0)
    print(f"Splits for $10.0: {splits}")
    assert splits["valid"] is True
    assert splits["search"] == 2.0
    assert splits["quality"] == 1.0
    assert splits["platform"] == 3.0
    
    low_budget_splits = manager.calculate_splits(6.0)
    print(f"Splits for $6.0: {low_budget_splits}")
    assert low_budget_splits["valid"] is False
    print("✅ Split calculation correct")

    print("\n--- Testing API Endpoints ---")
    client = app.test_client()
    
    # Test Analyze Query
    res = client.get('/api/analyze-query?query=Detailed market analysis and research report')
    data = res.get_json()
    print(f"Query Analysis: {data}")
    assert "tiers" in data
    assert data["complexity"] > 1
    
    # Test Get Profile
    res = client.get('/api/agents/profile/search_agent_v1')
    data = res.get_json()
    print(f"Profile: {data}")
    assert data["name"] == "Search Agent"
    
    # Test Add Review
    res = client.post('/api/agents/search_agent_v1/review', json={"rating": 5, "comment": "Excellent!"})
    print(f"Review Add: {res.get_json()}")
    assert res.status_code == 200
    
    # Check if review reflects in profile
    res = client.get('/api/agents/profile/search_agent_v1')
    data = res.get_json()
    print(f"Updated Profile (Rating): {data['rating']}")
    assert data["rating"] == 5.0
    
    print("✅ API endpoints functional")

    print("\n--- Testing Quality Agent Execution ---")
    res = manager.quality_agent.execute("Great report content")
    print(f"Quality Assessment: {res['quality_score']}/10")
    assert "quality_score" in res
    print("✅ Quality agent works")

if __name__ == "__main__":
    test_registration_system()
