import os
from dotenv import load_dotenv

load_dotenv()

# Configuration for AgentMarket
# This file centralizes all environment variables and constants.

LOCUS_API_KEY = os.getenv("LOCUS_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
LOCUS_API_BASE = "https://beta-api.paywithlocus.com/api"
