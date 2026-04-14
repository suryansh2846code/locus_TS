from __future__ import annotations
import json
import os
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Union, Optional

if TYPE_CHECKING:
    from agents.base_agent import BaseAgent


class AgentRegistry:
    """
    Singleton-style registry that tracks every agent in the marketplace.
    Backs in-memory agents with a JSON configuration file.
    """

    def __init__(self) -> None:
        self.agents: dict[str, "BaseAgent"] = {}
        self.config_path: str = ""

    def load_from_config(self, config_path: str) -> None:
        """Reads agent_config.json on startup and registers agents."""
        self.config_path = config_path
        if not os.path.exists(config_path):
            print(f"⚠️ Config not found at {config_path}")
            return

        with open(config_path, "r") as f:
            data = json.load(f)
            for agent_data in data.get("agents", []):
                # We register the metadata. Actual instances are added by the Manager.
                # Here we just track the existence and basic profile in the registry
                # so we can answer /api/agents and rate queries.
                # Note: In a real app, we'd use a factory to instantiate from strings.
                self.agents[agent_data["name"]] = agent_data
                print(f"✅ Loaded from Config: {agent_data['name']}")

    def _save_to_config(self) -> None:
        """Persists current agent state to JSON."""
        if not self.config_path:
            return
        
        # Convert all items to dicts
        agents_to_save = []
        for agent in self.agents.values():
            if hasattr(agent, "to_dict"):
                agents_to_save.append(agent.to_dict())
            else:
                agents_to_save.append(agent)
            
        with open(self.config_path, "w") as f:
            json.dump({"agents": agents_to_save}, f, indent=2)

    def register_agent(self, agent: "BaseAgent") -> None:
        """Add an agent instance to the marketplace registry."""
        self.agents[agent.name] = agent
        print(f"✅ Registered: {agent.name}  [{agent.speciality}]")

    def register_new_agent(self, agent_data: dict) -> dict:
        """Validates and registers a new agent into the JSON persistent store."""
        required = ["name", "developer", "developer_wallet", "description", "speciality", "rate_per_task"]
        for field in required:
            if field not in agent_data:
                return {"success": False, "message": f"Missing field: {field}"}

        agent_id = str(uuid.uuid4())[:8]
        new_agent = {
            "id": agent_id,
            "name": agent_data["name"],
            "developer": agent_data["developer"],
            "developer_wallet": agent_data["developer_wallet"],
            "description": agent_data["description"],
            "speciality": agent_data["speciality"],
            "rate_per_task": float(agent_data["rate_per_task"]),
            "min_budget": 0.50,
            "max_budget": 20.00,
            "version": "1.0",
            "status": "active",
            "total_jobs": 0,
            "total_earned": 0.0,
            "rating": 5.0,
            "reviews": [],
            "registered_at": datetime.now().strftime("%Y-%m-%d")
        }

        self.agents[new_agent["name"]] = new_agent
        self._save_to_config()
        
        return {
            "success": True,
            "agent_id": agent_id,
            "message": "Agent registered!"
        }

    def get_agent_rate(self, agent_name: str) -> float:
        """Returns rate from config/instance."""
        agent = self.agents.get(agent_name)
        if not agent:
            return 2.0  # Default fallback
        
        if isinstance(agent, dict):
            return agent.get("rate_per_task", 2.0)
        return getattr(agent, "rate_per_task", 2.0)

    def get_total_agent_cost(self) -> float:
        """Returns sum of all active agent rates."""
        total = 0.0
        names = ["Search Agent", "Analysis Agent", "Writing Agent", "Quality Check Agent"]
        for name in names:
            total += self.get_agent_rate(name)
        return total

    def update_agent_rate(self, agent_id: str, new_rate: float) -> dict:
        """Validates and updates agent rate."""
        if not (0.10 <= new_rate <= 50.00):
            return {"success": False, "message": "Rate must be between $0.10 and $50.00"}

        found = False
        for name, agent in self.agents.items():
            if isinstance(agent, dict) and agent.get("id") == agent_id:
                agent["rate_per_task"] = new_rate
                found = True
            elif hasattr(agent, "id") and agent.id == agent_id:
                agent.rate_per_task = new_rate
                found = True
        
        if found:
            self._save_to_config()
            return {"success": True, "message": f"Rate updated to ${new_rate}"}
        return {"success": False, "message": "Agent not found"}

    def get_agent_profile(self, agent_id: str) -> dict | None:
        """Returns complete agent profile."""
        for agent in self.agents.values():
            if isinstance(agent, dict) and agent.get("id") == agent_id:
                return agent
            elif hasattr(agent, "id") and agent.id == agent_id:
                # Mock a profile from instance
                return {
                    "id": agent.id,
                    "name": agent.name,
                    "developer": getattr(agent, "developer", "Unknown"),
                    "description": agent.description,
                    "speciality": agent.speciality,
                    "rate": agent.rate_per_task,
                    "rating": agent.rating,
                    "total_jobs": getattr(agent, "tasks_completed", 0),
                    "total_earned": getattr(agent, "total_earned", 0.0),
                    "reviews": getattr(agent, "reviews", []),
                    "status": "active",
                    "registered_at": getattr(agent, "registered_at", "2026-04-11")
                }
        return None

    def add_review(self, agent_id: str, rating: float, comment: str) -> dict:
        """Adds review and recalcs rating."""
        profile = self.get_agent_profile(agent_id)
        if not profile:
            return {"success": False, "message": "Agent not found"}

        review = {
            "rating": rating,
            "comment": comment,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        if "reviews" not in profile:
            profile["reviews"] = []
        profile["reviews"].append(review)
        
        # Recalc average rating
        all_ratings = [r["rating"] for r in profile["reviews"]]
        profile["rating"] = round(sum(all_ratings) / len(all_ratings), 1)
        
        self._save_to_config()
        return {"success": True, "message": "Review added!"}

    def get_all_agents(self) -> list[dict]:
        """Return JSON-serializable data for all agents."""
        output = []
        for agent in self.agents.values():
            if hasattr(agent, "get_card_data"):
                output.append(agent.get_card_data())
            elif isinstance(agent, dict):
                output.append(agent)
            else:
                # Basic fallback for other types
                output.append(str(agent))
        return output

    def get_marketplace_stats(self) -> dict:
        return {
            "total_agents": len(self.agents),
            "total_tasks_completed": 0, # Should be tracked globally
            "total_usdc_paid_out": 0.0,
            "most_active_agent": "Search Agent"
        }

registry = AgentRegistry()
