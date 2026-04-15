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

        # Prevent duplicate name registrations
        if agent_data["name"] in self.agents:
            return {"success": False, "message": f"Agent '{agent_data['name']}' is already registered."}

        # Deterministic ID from name: "Test News Agent" -> "test_news_agent_v1"
        slug = agent_data["name"].lower().replace(" ", "_")
        agent_id = f"{slug}_v1"
        # Ensure uniqueness if slug already exists
        existing_ids = [a.get("id", "") for a in self.agents.values() if isinstance(a, dict)]
        if agent_id in existing_ids:
            agent_id = f"{slug}_v{len(existing_ids) + 1}"
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
            "successful_jobs": 0,
            "total_earned": 0.0,
            "rating": 5.0,
            "reviews": [],
            "last_active_at": "Never",
            "registered_at": datetime.now().strftime("%Y-%m-%d")
        }

        self.agents[new_agent["name"]] = new_agent
        self._save_to_config()
        
        return {
            "success": True,
            "agent_id": agent_id,
            "message": "Agent registered successfully!"
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

    def update_agent_after_job(self, agent_name: str, success: bool, amount_earned: float) -> None:
        """Updates agent performance stats after a completed pipeline step."""
        agent = self.agents.get(agent_name)
        if not agent:
            print(f"⚠️ Registry: Agent '{agent_name}' not found for stats update.")
            return

        # Handle both dict (from config) and instance
        if isinstance(agent, dict):
            agent["total_jobs"] = agent.get("total_jobs", 0) + 1
            if success:
                agent["successful_jobs"] = agent.get("successful_jobs", 0) + 1
            
            agent["total_earned"] = round(agent.get("total_earned", 0.0) + amount_earned, 2)
            agent["last_active_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # Recalculate rating based on success rate if we have enough jobs
            if agent["total_jobs"] > 0:
                success_rate = agent["successful_jobs"] / agent["total_jobs"]
                agent["rating"] = round(success_rate * 5.0, 1)
        else:
            # If it's an instance, we update its attributes
            agent.tasks_completed = getattr(agent, "tasks_completed", 0) + 1
            agent.total_earned = round(getattr(agent, "total_earned", 0.0) + amount_earned, 2)
            # Find the dict version to sync back to config
            for a_name, a_data in self.agents.items():
                if isinstance(a_data, dict) and a_name == agent_name:
                    a_data["total_jobs"] = agent.tasks_completed
                    a_data["total_earned"] = agent.total_earned
                    if success:
                        a_data["successful_jobs"] = a_data.get("successful_jobs", 0) + 1
                    a_data["last_active_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    if a_data["total_jobs"] > 0:
                        success_rate = a_data["successful_jobs"] / a_data["total_jobs"]
                        a_data["rating"] = round(success_rate * 5.0, 1)

        self._save_to_config()
        print(f"📈 Updated stats for {agent_name}: Jobs={agent.get('total_jobs') if isinstance(agent, dict) else agent.tasks_completed}, Earned=${amount_earned}")

    def get_all_agents(self) -> list[dict]:
        """Return JSON-serializable data for all agents from persistent config."""
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                    return data.get("agents", [])
            except Exception as e:
                print(f"⚠️ Error reading config for agents display: {e}")
                
        # Fallback to memory
        output = []
        for agent in self.agents.values():
            if isinstance(agent, dict):
                output.append(agent)
            elif hasattr(agent, "get_card_data"):
                output.append(agent.get_card_data())
            else:
                output.append(str(agent))
        return output

    def get_marketplace_stats(self) -> dict:
        total_jobs = sum(a.get("total_jobs", 0) if isinstance(a, dict) else getattr(a, "tasks_completed", 0) for a in self.agents.values())
        total_earned = sum(a.get("total_earned", 0.0) if isinstance(a, dict) else getattr(a, "total_earned", 0.0) for a in self.agents.values())
        
        # Determine most active
        most_active = "None"
        max_jobs = -1
        for name, a in self.agents.items():
            jobs = a.get("total_jobs", 0) if isinstance(a, dict) else getattr(a, "tasks_completed", 0)
            if jobs > max_jobs:
                max_jobs = jobs
                most_active = name

        return {
            "total_agents": len(self.agents),
            "total_tasks_completed": total_jobs,
            "total_usdc_paid_out": round(total_earned, 2),
            "most_active_agent": most_active
        }

registry = AgentRegistry()
