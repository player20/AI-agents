from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import uuid
from datetime import datetime
from multi_agent_team import run_dev_team, agent_logs, AGENT_ROLES

app = Flask(__name__)
CORS(app)  # Allow React to call from localhost:3000

# In-memory storage for executions (simple MVP)
executions = {}

@app.route('/api/execute-team', methods=['POST'])
def execute_team():
    """
    Execute a team of agents sequentially.

    Request Body:
    {
        "projectId": "project-123",
        "teamId": "team-456",
        "agents": ["PM", "Senior", "Web"],
        "prompt": "Build an e-commerce platform",
        "previousOutputs": [...]  # Outputs from previous teams
    }

    Response:
    {
        "executionId": "exec-789",
        "status": "running",
        "teamId": "team-456",
        "message": "Team execution started"
    }
    """
    data = request.json

    # Validate required fields
    required = ['agents', 'prompt']
    if not all(key in data for key in required):
        return jsonify({"error": "Missing required fields"}), 400

    # Validate agents (warn about unknown agents but allow execution)
    unknown_agents = [a for a in data['agents'] if a not in AGENT_ROLES]
    if unknown_agents:
        print(f"⚠️  Warning: Custom agents detected: {', '.join(unknown_agents)}")
        print(f"   These agents will be created as generic agents")
        print(f"   Known agents: {', '.join(AGENT_ROLES)}")

    # Create execution record
    execution_id = f"exec-{uuid.uuid4().hex[:8]}"
    execution = {
        "id": execution_id,
        "projectId": data.get('projectId'),
        "teamId": data.get('teamId'),
        "agents": data['agents'],
        "prompt": data['prompt'],
        "previousOutputs": data.get('previousOutputs', []),
        "status": "running",
        "startedAt": datetime.now().isoformat(),
        "progress": 0
    }
    executions[execution_id] = execution

    # Run agents in background thread
    def run_background():
        try:
            # Build context from previous outputs
            context = data['prompt']
            if data.get('previousOutputs'):
                context += "\n\n=== Context from Previous Teams ===\n"
                for prev in data['previousOutputs']:
                    context += f"\n## {prev['teamName']} Output:\n{prev['output']}\n"

            # Execute agents via existing run_dev_team function
            status_msg, outputs, export_paths = run_dev_team(
                project_description=context,
                selected_agents=data['agents'],
                custom_prompts={},
                agent_models={},
                execution_priorities={},
                model_preset="Balanced (All Sonnet)",
                code_review_mode=False,
                phase="Full Run (All Agents)",
                auto_export=False,
                feedback="",
                approval="approve",
                github_url=""
            )

            # Parse outputs into structured format
            agent_outputs = []
            combined_output = ""
            for agent_id in data['agents']:
                output_text = outputs.get(agent_id, "")
                if output_text:
                    agent_outputs.append({
                        "agentId": agent_id,
                        "output": output_text
                    })
                    combined_output += f"\n\n=== {agent_id} ===\n{output_text}"

            # Update execution record
            execution["status"] = "completed"
            execution["completedAt"] = datetime.now().isoformat()
            execution["outputs"] = agent_outputs
            execution["combinedOutput"] = combined_output.strip()
            execution["duration"] = 0  # TODO: Track actual duration
            execution["cost"] = 0  # TODO: Calculate actual cost
            execution["progress"] = 100

        except Exception as e:
            execution["status"] = "failed"
            execution["error"] = str(e)
            execution["completedAt"] = datetime.now().isoformat()

    thread = threading.Thread(target=run_background)
    thread.start()

    return jsonify({
        "executionId": execution_id,
        "status": "running",
        "teamId": data.get('teamId'),
        "message": f"Executing {len(data['agents'])} agents"
    }), 202

@app.route('/api/status/<execution_id>', methods=['GET'])
def get_status(execution_id):
    """Get execution status and results."""
    if execution_id not in executions:
        return jsonify({"error": "Execution not found"}), 404

    execution = executions[execution_id]
    return jsonify(execution)

@app.route('/api/agents', methods=['GET'])
def list_agents():
    """List available agents."""
    agents = [
        {"id": role, "label": role, "available": True}
        for role in AGENT_ROLES
    ]
    return jsonify({"agents": agents})

@app.route('/api/agents/validate', methods=['POST'])
def validate_agents():
    """
    Validate a list of agent IDs and categorize them as known or custom.

    Request Body:
    {
        "agents": ["PM", "Senior", "DevOps"]  // Agent IDs to validate
    }

    Response:
    {
        "valid": ["PM", "Senior"],       // Known agents
        "custom": ["DevOps"],            // Custom/unknown agents
        "warnings": [                    // Warning messages
            "Agent 'DevOps' not in standard config"
        ]
    }
    """
    data = request.json
    agents = data.get('agents', [])

    result = {
        "valid": [],
        "custom": [],
        "warnings": []
    }

    for agent_id in agents:
        if agent_id in AGENT_ROLES:
            result["valid"].append(agent_id)
        else:
            result["custom"].append(agent_id)
            result["warnings"].append(f"Agent '{agent_id}' not in standard config")

    return jsonify(result)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "multi-agent-backend"})

if __name__ == '__main__':
    print("🚀 Starting Multi-Agent API Backend...")
    print("📡 API available at: http://localhost:7860")
    print("🔗 CORS enabled for: http://localhost:3000")
    app.run(host='0.0.0.0', port=7860, debug=True, threaded=True)
