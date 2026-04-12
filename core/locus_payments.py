import requests
import os
from config import LOCUS_API_KEY, LOCUS_API_BASE

SEARCH_AGENT_WALLET = os.getenv("SEARCH_AGENT_WALLET")
ANALYSIS_AGENT_WALLET = os.getenv("ANALYSIS_AGENT_WALLET")
WRITING_AGENT_WALLET = os.getenv("WRITING_AGENT_WALLET")

print(f"📡 Wallet Loaded - Search Agent: {SEARCH_AGENT_WALLET}")
print(f"📡 Wallet Loaded - Analysis Agent: {ANALYSIS_AGENT_WALLET}")
print(f"📡 Wallet Loaded - Writing Agent: {WRITING_AGENT_WALLET}")

# Base headers for all Locus API requests
HEADERS = {
    "Authorization": f"Bearer {LOCUS_API_KEY}",
    "Content-Type": "application/json"
}

def get_balance():
    """
    Fetches the current USDC balance from /api/pay/balance.
    Returns: float balance
    """
    url = f"{LOCUS_API_BASE}/pay/balance"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            balance = float(data["data"]["usdc_balance"])
            print(f"💰 Current Locus Balance: {balance} USDC")
            return balance
        else:
            print(f"❌ Failed to get balance: {data.get('message')}")
            return 0.0
    except Exception as e:
        print(f"Error in get_balance: {e}")
        return 0.0

def pay_agent(to_address, amount, agent_name, task):
    """
    Sends USDC to an agent's wallet via /api/pay/send.
    Returns: transaction_id (str) or None
    """
    url = f"{LOCUS_API_BASE}/pay/send"
    
    # Update to_address based on agent_name
    if agent_name in ["SearchAgent", "Search Agent"]:
        to_address = SEARCH_AGENT_WALLET
    elif agent_name in ["AnalysisAgent", "Analysis Agent"]:
        to_address = ANALYSIS_AGENT_WALLET
    elif agent_name in ["WritingAgent", "Writing Agent"]:
        to_address = WRITING_AGENT_WALLET
        
    memo = f"Hiring {agent_name} for {task}"
    payload = {
        "to_address": to_address,
        "amount": amount,
        "memo": memo
    }
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload)
        response.raise_for_status()
        data = response.json()
        
        if data.get("success"):
            tx_id = data["data"].get("transaction_id")
            status = data["data"].get("status")
            print(f"✅ Paid {agent_name} ${amount} for {task}")
            print(f"   Status: {status} | Tx ID: {tx_id}")
            return tx_id
        else:
            print(f"❌ Payment failed: {data.get('message')}")
            return None
    except Exception as e:
        print(f"Error in pay_agent: {e}")
        return None

def get_transaction_history():
    """
    Fetches transaction history from /api/pay/transactions.
    Returns: list of simplified transaction objects
    """
    url = f"{LOCUS_API_BASE}/pay/transactions"
    params = {"limit": 50}
    
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get("success"):
            api_txs = data["data"].get("transactions", [])
            # Map to requested format: id, from, to, amount, memo, timestamp, status
            formatted_txs = []
            for tx in api_txs:
                formatted_txs.append({
                    "id": tx.get("id"),
                    "from": "0xYourWallet...", # API doesn't always return 'from' in detail list
                    "to": tx.get("to_address"),
                    "amount": tx.get("amount_usdc"),
                    "memo": tx.get("memo"),
                    "timestamp": tx.get("created_at"),
                    "status": tx.get("status")
                })
            return formatted_txs
        else:
            print(f"❌ Failed to fetch history: {data.get('message')}")
            return []
    except Exception as e:
        print(f"Error in get_transaction_history: {e}")
        return []

def request_credits(reason, amount):
    """
    Requests promotional hackathon credits via /api/gift-code-requests.
    Returns: bool (success/failure)
    """
    url = f"{LOCUS_API_BASE}/gift-code-requests"
    payload = {
        "reason": reason,
        "requestedAmountUsdc": amount,
        "githubUrl": "https://github.com/suryansh2846code/locus_TS.git" # Required by API
    }
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload)
        # 429 is common for this endpoint if requested recently
        if response.status_code == 429:
            print("🕒 Credit request rate limited (1 per 24h).")
            return False
            
        data = response.json()
        if data.get("success"):
            print(f"🤝 Credit request for ${amount} submitted successfully!")
            return True
        else:
            print(f"❌ Credit request failed: {data.get('message')}")
            return False
    except Exception as e:
        print(f"Error in request_credits: {e}")
        return False
