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
    budget = float(data.get("budget", 0.0))
    
    if not query:
        return jsonify({"success": False, "error": "Query is required"}), 400

    print(f"📡 API research request started: {query} (${budget})")
    
    # Consume the generator fully
    final_result = {}
    for update in manager.process_request(query, budget):
        if update.get("step") == "error":
            return jsonify(update.get("result", {})), 400
        if update.get("step") == "done":
            final_result = update.get("result", {})
    
    return jsonify(final_result)

@app.route('/api/stream', methods=['GET'])
def stream():
    """SSE endpoint for real-time manager updates."""
    query = request.args.get("query")
    budget = float(request.args.get("budget", 0.0))
    
    if not query:
        return jsonify({"success": False, "error": "Query is required"}), 400

    def event_stream():
        print(f"📡 SSE stream started: {query} (${budget})")
        for update in manager.process_request(query, budget):
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
    marketplace_status = manager.get_status()
    marketplace_status["api_status"] = "healthy"
    return jsonify(marketplace_status)

def print_routes():
    print("\n🌐 AgentMarket API Routes Loaded:")
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            print(f"   [{', '.join(rule.methods)}] {rule.rule} -> {rule.endpoint}")
    print("\n🚀 Server starting on http://localhost:5001\n")

if __name__ == '__main__':
    print_routes()
    # Using 5001 to avoid macOS AirPlay conflict on 5000
    app.run(host='0.0.0.0', port=5001, threaded=True)
