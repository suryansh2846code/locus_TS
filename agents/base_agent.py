# base_agent.py
# Abstract base class for all marketplace agents.
# Defines the common interface for task execution and payment receiving.

class BaseAgent:
    def __init__(self, name, wallet_address, price):
        self.name = name
        self.wallet_address = wallet_address
        self.price = price

    def execute_task(self, data):
        """Method to be overridden by subclasses."""
        raise NotImplementedError("Subclasses must implement execute_task")
