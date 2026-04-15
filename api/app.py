import sys
import os
import json
from flask import Flask, jsonify, request, Response
from flask_cors import CORS

# Add the project root to sys.path to allow imports from core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.locus_payments import get_balance, get_transaction_history
from core.manager_agent import ManagerAgent

app = Flask(__name__)
CORS(app)

# Initialize the marketplace brain singleton
manager = ManagerAgent()

@app.route('/', methods=['GET'])
def index():
    """Returns basic platform info."""
    return jsonify({
        "status": "AgentMarket running!",
        "version": "1.0",
        "marketplace": "Locus Paygentic Hackathon"
    })

@app.route('/api/research', methods=['POST'])
def research():
    """Triggers the full agent research pipeline and returns a complete result."""
    data = request.json
    query = data.get("query")
    
    if not query:
        return jsonify({"success": False, "error": "Query is required"}), 400

    print(f"📡 API research request started: {query}")
    
    # Consume the generator fully
    final_result = {}
    for update in manager.process_request(query):
        if update.get("step") == "error":
            return jsonify(update.get("result", {})), 402 if update.get("error") == "insufficient_balance" else 400
        if update.get("step") == "done":
            final_result = update.get("result", {})
    
    return jsonify(final_result)

@app.route('/api/stream', methods=['GET'])
def stream():
    """SSE endpoint for real-time manager updates."""
    query = request.args.get("query")
    
    if not query:
        return jsonify({"success": False, "error": "Query is required"}), 400

    def event_stream():
        print(f"📡 SSE stream started: {query}")
        for update in manager.process_request(query):
            # Format as SSE data
            yield f"data: {json.dumps(update)}\n\n"
        
    return Response(event_stream(), mimetype='text/event-stream')

@app.route('/api/balance', methods=['GET'])
def balance():
    """Returns the current Locus USDC balance."""
    current_balance = get_balance()
    return jsonify({"balance": current_balance})

@app.route('/api/transactions', methods=['GET'])
def transactions():
    """Returns the transaction history."""
    history = get_transaction_history()
    return jsonify({"transactions": history})

@app.route('/api/agents', methods=['GET'])
def agents():
    """Returns all registered agents and their stats."""
    all_agents = manager.registry.get_all_agents()
    return jsonify({"agents": all_agents})

@app.route('/api/status', methods=['GET'])
def status():
    """Returns marketplace health status."""
    try:
        marketplace_status = manager.get_status()
        marketplace_status["api_status"] = "healthy"
        return jsonify(marketplace_status)
    except Exception as e:
        print(f"ERROR in /api/status: {e}", file=sys.stderr)
        return jsonify({
            "api_status": "degraded",
            "error": str(e),
            "total_agents": 0,
            "wallet_balance": 0.0
        }), 200 # Return 200 so the frontend doesn't show the red banner

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Returns the completed job history from jobs.json."""
    history_path = os.path.join(os.path.dirname(__file__), '..', 'jobs.json')
    if os.path.exists(history_path):
        with open(history_path, 'r') as f:
            try:
                data = json.load(f)
                return jsonify(data)
            except Exception:
                pass
    return jsonify({"jobs": []})

@app.route('/api/register-agent', methods=['POST'])
def register_agent():
    """Registers a new agent."""
    data = request.json
    result = manager.registry.register_new_agent(data)
    return jsonify(result), 200 if result["success"] else 400

@app.route('/api/agents/profile/<agent_id>', methods=['GET'])
def get_agent_profile(agent_id):
    """Returns complete agent profile."""
    profile = manager.registry.get_agent_profile(agent_id)
    if profile:
        return jsonify(profile)
    return jsonify({"success": False, "message": "Agent not found"}), 404

@app.route('/api/agents/<agent_id>/rate', methods=['PUT'])
def update_agent_rate(agent_id):
    """Updates agent rate."""
    data = request.json
    new_rate = data.get("new_rate")
    if new_rate is None:
        return jsonify({"success": False, "message": "new_rate is required"}), 400
    result = manager.registry.update_agent_rate(agent_id, float(new_rate))
    return jsonify(result), 200 if result["success"] else 400

@app.route('/api/agents/<agent_id>/review', methods=['POST'])
def add_agent_review(agent_id):
    """Adds a review for an agent."""
    data = request.json
    rating = data.get("rating")
    comment = data.get("comment", "")
    if rating is None:
        return jsonify({"success": False, "message": "rating is required"}), 400
    result = manager.registry.add_review(agent_id, float(rating), comment)
    return jsonify(result), 200 if result["success"] else 400

@app.route('/api/analyze-query', methods=['GET'])
def analyze_query_endpoint():
    """Analyzes query complexity and returns dynamically selected agents."""
    query = request.args.get("query", "")
    if not query:
        return jsonify({"success": False, "message": "query is required"}), 400
    
    # BUDGET_TIERS_DISABLED_START
    # word_count = len(query.split())
    # complex_keywords = [
    #     "analysis", "research", "comprehensive", "detailed", "compare", 
    #     "market", "industry", "report", "trends", "forecast", "strategy", "deep"
    # ]
    # 
    # complexity = sum(1 for w in complex_keywords if w in query.lower())
    # complexity += min(word_count // 5, 3)
    # 
    # # Get real agent rates from config
    # base_cost = manager.registry.get_total_agent_cost()
    # 
    # if complexity <= 2:
    #     low, medium, high = base_cost + 0.10, base_cost + 0.60, base_cost + 1.60
    #     recommended = "low"
    # elif complexity <= 5:
    #     low, medium, high = base_cost + 1.00, base_cost + 3.00, base_cost + 7.00
    #     recommended = "medium"
    # else:
    #     low, medium, high = base_cost + 2.00, base_cost + 5.00, base_cost + 10.00
    #     recommended = "high"
    # 
    # result = {
    #     "complexity": complexity,
    #     "recommended": recommended,
    #     "tiers": {
    #         "low": {
    #             "amount": round(low, 2),
    #             "label": "💚 Basic",
    #             "quality": "Overview",
    #             "description": "Quick summary of main points"
    #         },
    #         "medium": {
    #             "amount": round(medium, 2),
    #             "label": "💛 Standard",
    #             "quality": "Detailed",
    #             "description": "Thorough research recommended ✨"
    #         },
    #         "high": {
    #             "amount": round(high, 2),
    #             "label": "❤️ Premium",
    #             "quality": "Comprehensive",
    #             "description": "In-depth analysis and insights"
    #         }
    #     }
    # }
    # BUDGET_TIERS_DISABLED_END

    # Call the master agent routing logic
    selected_agent_ids = manager.select_agents(query)
    
    # Ensure quality agent is at the end
    if "quality_agent" in selected_agent_ids:
        selected_agent_ids.remove("quality_agent")
    selected_agent_ids.append("quality_agent")
    
    splits = manager.calculate_splits_dynamic(selected_agent_ids)
    
    agent_details = []
    for a_id in selected_agent_ids:
        agent = manager.agent_map[a_id]
        rate = splits["costs"][a_id]
        agent_details.append({
            "id": a_id,
            "name": agent.name,
            "rate": rate
        })
        
    estimated_cost = splits["total_agent_cost"]
    platform_fee = splits["platform"]
    total_with_fee = splits["estimated_cost"]
    current_balance = get_balance()
    
    result = {
        "agents": selected_agent_ids,
        "agent_details": agent_details,
        "estimated_cost": estimated_cost,
        "balance": current_balance,
        "affordable": current_balance >= total_with_fee,
        "platform_fee": platform_fee,
        "total_with_fee": total_with_fee
    }
    
    return jsonify(result)

def print_routes():
    print("\n🌐 AgentMarket API Routes Loaded:")
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            print(f"   [{', '.join(rule.methods)}] {rule.rule} -> {rule.endpoint}")
    print("\n🚀 Server starting on http://127.0.0.1:5001\n")

if __name__ == '__main__':
    print_routes()
    # Using 5001 to avoid macOS AirPlay conflict on 5000
    app.run(host='0.0.0.0', port=5001, threaded=True)
