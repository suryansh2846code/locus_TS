# agent_registry.py
# Registry of available agents in the marketplace.
# Stores agent capabilities, wallet addresses, and pricing.

class AgentRegistry:
    def __init__(self):
        # Store agents as a list of dictionaries
        self.agents = []

    def register_agent(self, name, capabilities, wallet_address, price):
        """Registers a new agent to the marketplace."""
        agent = {
            "name": name,
            "capabilities": capabilities,
            "wallet_address": wallet_address,
            "price": price
        }
        self.agents.append(agent)
        print(f"📦 Registered {name} to Marketplace Registry.")

    def get_agent_by_capability(self, capability):
        """Returns the first agent matching the capability."""
        for agent in self.agents:
            if capability in agent["capabilities"]:
                return agent
        return None

    def get_all_agents(self):
        """Returns all registered agents."""
        return self.agents
