"""
agents/base_agent.py
────────────────────
Abstract base class for every specialist agent in the AgentMarket marketplace.

All specialist agents (SearchAgent, WritingAgent, AnalysisAgent, …) must
inherit from BaseAgent and override the `execute()` method.

Lifecycle of a task
───────────────────
  1. Caller invokes agent.execute(task)        ← overridden by subclass
  2. Subclass performs work, returns result
  3. Caller invokes agent.update_stats(success, amount_earned)
  4. agent.get_stats() / get_card_data() reflect updated state
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union


class BaseAgent(ABC):
    """
    Abstract foundation for all AgentMarket marketplace agents.

    Parameters
    ----------
    name : str
        Human-readable agent identifier (must be unique in the registry).
    description : str
        A short sentence explaining what the agent does.
    speciality : str
        Domain tag (e.g. "research", "writing", "analysis").
    rate_per_task : float
        USDC price charged per individual task execution.
    """

    # ------------------------------------------------------------------ #
    #  Construction                                                         #
    # ------------------------------------------------------------------ #

    def __init__(
        self,
        name: str,
        description: str,
        speciality: str,
        rate_per_task: float,
        agent_id: Optional[str] = None,
        developer: str = "Unknown",
        developer_wallet: str = "",
        min_budget: float = 0.50,
        max_budget: float = 20.00,
        version: str = "1.0",
        registered_at: str = "",
    ) -> None:
        # Core identity
        self.id: str = agent_id or name.lower().replace(" ", "_")
        self.name: str = name
        self.description: str = description
        self.speciality: str = speciality
        self.rate_per_task: float = rate_per_task
        
        # Developer & Lifecycle
        self.developer: str = developer
        self.developer_wallet: str = developer_wallet
        self.min_budget: float = min_budget
        self.max_budget: float = max_budget
        self.version: str = version
        self.status: str = "active"
        self.registered_at: str = registered_at

        # Set later (after wallet provisioning via Locus)
        self.wallet_address: str = ""

        # Lifetime performance counters
        self.tasks_completed: int = 0
        self.successful_tasks: int = 0
        self.total_earned: float = 0.0

        # Reviews & Ratings
        self.reviews: list[dict] = []
        self.rating: float = 5.0

    # ------------------------------------------------------------------ #
    #  Abstract interface — MUST be overridden by subclasses               #
    # ------------------------------------------------------------------ #

    @abstractmethod
    def execute(self, task: str) -> str:
        """
        Execute the given task and return a result string.

        Parameters
        ----------
        task : str
            Natural-language description of work to perform.

        Returns
        -------
        str
            The agent's output / result for the requested task.

        Raises
        ------
        NotImplementedError
            Automatically raised by ABC machinery if a concrete subclass
            forgets to override this method.
        """
        raise NotImplementedError(
            f"Agent '{self.name}' has not implemented execute(). "
            "All BaseAgent subclasses must override this method."
        )

    # ------------------------------------------------------------------ #
    #  Stats & lifecycle                                                    #
    # ------------------------------------------------------------------ #

    def update_stats(self, success: bool, amount_earned: float) -> None:
        """
        Record the outcome of a completed task and refresh the agent's rating.

        Call this **after** every `execute()` call, whether successful or not.

        Parameters
        ----------
        success : bool
            True if the task completed without errors; False otherwise.
        amount_earned : float
            USDC amount received for this task (0.0 on failure is fine).
        """
        self.tasks_completed += 1

        if success:
            self.successful_tasks += 1

        self.total_earned += amount_earned

        # Rating = (successful / total) * 5  — floored at 0.0, capped at 5.0
        if self.tasks_completed > 0:
            raw = (self.successful_tasks / self.tasks_completed) * 5.0
            self.rating = round(max(0.0, min(5.0, raw)), 2)

    def get_stats(self) -> dict[str, Any]:
        """
        Return a complete runtime snapshot of the agent's performance.

        Returns
        -------
        dict with keys:
            name, rating, tasks_completed, success_rate,
            total_earned, status
        """
        return {
            "name": self.name,
            "rating": self.rating,
            "tasks_completed": self.tasks_completed,
            "success_rate": self._success_rate(),
            "total_earned": round(self.total_earned, 4),
            "status": self._status(),
        }

    def get_card_data(self) -> dict[str, Any]:
        """
        Return the subset of agent data used to render a marketplace UI card.

        Returns
        -------
        dict with keys:
            name, description, speciality, rate_per_task,
            rating, tasks_completed, success_rate, status
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "speciality": self.speciality,
            "rate_per_task": self.rate_per_task,
            "rating": self.rating,
            "tasks_completed": self.tasks_completed,
            "success_rate": self._success_rate(),
            "status": self.status,
        }

    def to_dict(self) -> dict[str, Any]:
        """Returns a full dictionary representation for JSON persistence."""
        return {
            "id": self.id,
            "name": self.name,
            "developer": self.developer,
            "developer_wallet": self.developer_wallet,
            "description": self.description,
            "speciality": self.speciality,
            "rate_per_task": self.rate_per_task,
            "min_budget": self.min_budget,
            "max_budget": self.max_budget,
            "version": self.version,
            "status": self.status,
            "total_jobs": self.tasks_completed,
            "total_earned": self.total_earned,
            "rating": self.rating,
            "reviews": self.reviews,
            "registered_at": self.registered_at
        }

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _success_rate(self) -> float:
        """Percentage of tasks that completed successfully (0–100)."""
        if self.tasks_completed == 0:
            return 100.0  # No tasks yet → optimistic default
        return round((self.successful_tasks / self.tasks_completed) * 100, 2)

    def _status(self) -> str:
        """Derive a human-readable status from current stats."""
        if self.tasks_completed == 0:
            return "new"
        if self._success_rate() >= 80:
            return "available"
        return "degraded"

    # ------------------------------------------------------------------ #
    #  Dunder helpers                                                       #
    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} name={self.name!r} "
            f"speciality={self.speciality!r} "
            f"rate={self.rate_per_task} USDC "
            f"rating={self.rating}/5.0>"
        )

    def __str__(self) -> str:
        return (
            f"{self.name} [{self.speciality}] "
            f"— {self.rate_per_task} USDC/task "
            f"— rating {self.rating}/5.0"
        )
