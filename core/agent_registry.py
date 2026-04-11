"""
core/agent_registry.py
───────────────────────
Central registry for all AgentMarket marketplace agents.

Agents self-register at startup. The registry is the single source of truth
for agent discovery, marketplace stats, and routing hire requests to the
correct specialist.

Usage
─────
    from core.agent_registry import registry          # global singleton
    from agents.search_agent import SearchAgent

    registry.register_agent(SearchAgent(...))
    all_cards = registry.get_all_agents()             # for /api/agents
    agent     = registry.get_agent("SearchAgent")
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agents.base_agent import BaseAgent


class AgentRegistry:
    """
    Singleton-style registry that tracks every agent in the marketplace.

    Agents are keyed by their `name` property (case-sensitive).
    """

    # ------------------------------------------------------------------ #
    #  Construction                                                         #
    # ------------------------------------------------------------------ #

    def __init__(self) -> None:
        self.agents: dict[str, "BaseAgent"] = {}

    # ------------------------------------------------------------------ #
    #  Registration                                                         #
    # ------------------------------------------------------------------ #

    def register_agent(self, agent: "BaseAgent") -> None:
        """
        Add an agent to the marketplace registry.

        Parameters
        ----------
        agent : BaseAgent
            Any concrete subclass of BaseAgent.

        Raises
        ------
        ValueError
            If an agent with that name is already registered.
        """
        if agent.name in self.agents:
            raise ValueError(
                f"Agent '{agent.name}' is already registered. "
                "Use a unique name or deregister the existing one first."
            )
        self.agents[agent.name] = agent
        print(f"✅ Registered: {agent.name}  [{agent.speciality}]  "
              f"@ {agent.rate_per_task} USDC/task")

    def deregister_agent(self, name: str) -> None:
        """
        Remove an agent from the registry by name.

        Parameters
        ----------
        name : str
            The `name` attribute of the agent to remove.

        Raises
        ------
        KeyError
            If no agent with that name exists.
        """
        if name not in self.agents:
            raise KeyError(f"No agent named '{name}' found in the registry.")
        del self.agents[name]
        print(f"🗑️  Deregistered: {name}")

    # ------------------------------------------------------------------ #
    #  Lookup                                                               #
    # ------------------------------------------------------------------ #

    def get_agent(self, name: str) -> "BaseAgent":
        """
        Retrieve a registered agent by its exact name.

        Parameters
        ----------
        name : str
            The `name` attribute of the desired agent.

        Returns
        -------
        BaseAgent

        Raises
        ------
        KeyError
            If no agent with that name is registered.
        """
        if name not in self.agents:
            available = ", ".join(self.agents.keys()) or "(none)"
            raise KeyError(
                f"Agent '{name}' not found in registry. "
                f"Available agents: {available}"
            )
        return self.agents[name]

    def get_agents_by_speciality(self, speciality: str) -> list["BaseAgent"]:
        """
        Filter registered agents by speciality tag.

        Parameters
        ----------
        speciality : str
            The speciality string to match (case-insensitive).

        Returns
        -------
        list[BaseAgent]
            All agents whose speciality matches (may be empty).
        """
        return [
            a for a in self.agents.values()
            if a.speciality.lower() == speciality.lower()
        ]

    # ------------------------------------------------------------------ #
    #  Marketplace data                                                     #
    # ------------------------------------------------------------------ #

    def get_all_agents(self) -> list[dict[str, Any]]:
        """
        Return card data for every registered agent.

        Used by the ``GET /api/agents`` endpoint to populate the
        marketplace frontend.

        Returns
        -------
        list[dict]
            One dict per agent (see BaseAgent.get_card_data for schema).
        """
        return [agent.get_card_data() for agent in self.agents.values()]

    def get_marketplace_stats(self) -> dict[str, Any]:
        """
        Aggregate statistics across the entire marketplace.

        Returns
        -------
        dict with keys:
            total_agents          – int
            total_tasks_completed – int
            total_usdc_paid_out   – float
            most_active_agent     – str | None
        """
        all_agents = list(self.agents.values())

        total_tasks = sum(a.tasks_completed for a in all_agents)
        total_usdc = round(sum(a.total_earned for a in all_agents), 4)

        most_active: str | None = None
        if all_agents:
            top = max(all_agents, key=lambda a: a.tasks_completed)
            most_active = top.name if top.tasks_completed > 0 else None

        return {
            "total_agents": len(all_agents),
            "total_tasks_completed": total_tasks,
            "total_usdc_paid_out": total_usdc,
            "most_active_agent": most_active,
        }

    # ------------------------------------------------------------------ #
    #  Dunder helpers                                                       #
    # ------------------------------------------------------------------ #

    def __len__(self) -> int:
        return len(self.agents)

    def __contains__(self, name: str) -> bool:
        return name in self.agents

    def __repr__(self) -> str:
        return f"<AgentRegistry agents={list(self.agents.keys())}>"


# ---------------------------------------------------------------------------
# Global singleton — import and use anywhere:
#   from core.agent_registry import registry
# ---------------------------------------------------------------------------
registry = AgentRegistry()
