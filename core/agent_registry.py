# agent_registry.py
# Registry of available agents in the marketplace.
# Stores agent capabilities, wallet addresses, and pricing.

class AgentRegistry:
    def __init__(self):
        self.agents = []

    def register_agent(self, name, capabilities, wallet_address, price):
        """Registers a new agent to the marketplace."""
        pass

    def get_agents_by_capability(self, capability):
        """Returns a list of agents capable of a specific task."""
        pass
