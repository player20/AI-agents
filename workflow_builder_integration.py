"""
Gradio Integration for Visual Workflow Builder

This module provides integration between the React-based Visual Workflow Builder
and the existing Gradio-based Multi-Agent Platform.

Includes REST API endpoints for dynamic agent management.

Usage:
    python workflow_builder_integration.py
"""

import gradio as gr
import subprocess
import os
import json
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS
import threading

# Path to workflow builder
WORKFLOW_BUILDER_DIR = Path(__file__).parent / "workflow_builder"
AGENTS_CONFIG_PATH = WORKFLOW_BUILDER_DIR / "src" / "config" / "agents.config.json"

# Create Flask API server
api_app = Flask(__name__)
CORS(api_app)  # Enable CORS for React app to call API


# ============================================================================
# REST API Endpoints
# ============================================================================

@api_app.route('/api/agents', methods=['GET'])
def get_agents():
    """
    Fetch list of available agents from config file.

    Returns:
        JSON object with agent configuration
    """
    try:
        if not AGENTS_CONFIG_PATH.exists():
            return jsonify({
                'error': 'Agent configuration file not found',
                'path': str(AGENTS_CONFIG_PATH)
            }), 404

        with open(AGENTS_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)

        return jsonify(config), 200

    except json.JSONDecodeError as e:
        return jsonify({
            'error': 'Invalid JSON in agent configuration',
            'details': str(e)
        }), 500

    except Exception as e:
        return jsonify({
            'error': 'Failed to load agent configuration',
            'details': str(e)
        }), 500


@api_app.route('/api/agents/validate', methods=['POST'])
def validate_agent():
    """
    Validate if an agent type is registered in the platform.

    Request Body:
        {
            "agent_id": "DevOps"
        }

    Returns:
        {
            "valid": true/false,
            "warning": "message if invalid"
        }
    """
    try:
        data = request.get_json()

        if not data or 'agent_id' not in data:
            return jsonify({
                'error': 'Missing required field: agent_id'
            }), 400

        agent_id = data['agent_id']

        # Load agent configuration
        if not AGENTS_CONFIG_PATH.exists():
            return jsonify({
                'error': 'Agent configuration file not found'
            }), 404

        with open(AGENTS_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Check if agent exists in built-in agents
        is_valid = any(agent['id'] == agent_id for agent in config.get('agents', []))

        response = {
            'valid': is_valid,
            'agent_id': agent_id
        }

        if not is_valid:
            response['warning'] = f"Agent '{agent_id}' is not registered in the platform."

        return jsonify(response), 200

    except json.JSONDecodeError as e:
        return jsonify({
            'error': 'Invalid JSON in agent configuration',
            'details': str(e)
        }), 500

    except Exception as e:
        return jsonify({
            'error': 'Validation failed',
            'details': str(e)
        }), 500


@api_app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for API server.

    Returns:
        {
            "status": "healthy",
            "version": "1.0.0"
        }
    """
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'service': 'Multi-Agent Workflow Builder API'
    }), 200


def start_api_server():
    """
    Start the Flask API server in a background thread.
    Runs on port 5000 by default.
    """
    print("[API] Starting REST API server on http://localhost:5000")
    api_app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False  # Disable reloader to avoid issues with threads
    )


# ============================================================================
# Workflow Builder Management
# ============================================================================

def start_workflow_builder():
    """
    Start the React workflow builder dev server.
    This should be called before launching the Gradio interface.
    """
    if not WORKFLOW_BUILDER_DIR.exists():
        print("[ERROR] Workflow builder directory not found!")
        print(f"Expected location: {WORKFLOW_BUILDER_DIR}")
        return False

    # Check if node_modules exists
    node_modules = WORKFLOW_BUILDER_DIR / "node_modules"
    if not node_modules.exists():
        print("[SETUP] Installing workflow builder dependencies...")
        subprocess.run(
            ["npm", "install"],
            cwd=WORKFLOW_BUILDER_DIR,
            check=True
        )

    # Start React dev server in background
    print("[START] Launching workflow builder at http://localhost:3000")
    subprocess.Popen(
        ["npm", "start"],
        cwd=WORKFLOW_BUILDER_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return True


def create_workflow_builder_tab():
    """
    Create a Gradio tab with the visual workflow builder embedded.

    Returns:
        Gradio Blocks component with workflow builder iframe
    """
    with gr.Blocks() as workflow_tab:
        gr.Markdown("## Visual Workflow Builder")
        gr.Markdown(
            "Create agent workflows visually by dragging and dropping agents onto the canvas."
        )

        # Embed workflow builder in iframe
        gr.HTML(
            """
            <iframe
                src="http://localhost:3000"
                width="100%"
                height="800px"
                frameborder="0"
                style="border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"
            ></iframe>
            """
        )

        gr.Markdown("### Quick Tips")
        gr.Markdown(
            """
            - **Drag agents** from the left palette onto the canvas
            - **Connect agents** by dragging from output (bottom) to input (top)
            - **Click an agent** to edit its prompt and model in the properties panel
            - **Export workflows** to YAML format compatible with template system
            - **Import workflows** from existing YAML templates
            """
        )

    return workflow_tab


def create_standalone_interface():
    """
    Create a standalone Gradio interface with just the workflow builder.
    Useful for testing or as a separate deployment.
    """
    with gr.Blocks(title="Multi-Agent Workflow Builder") as demo:
        gr.Markdown("# Multi-Agent Workflow Builder")

        workflow_tab = create_workflow_builder_tab()

    return demo


def integrate_with_existing_platform(demo):
    """
    Integrate workflow builder as a new tab in the existing Gradio platform.

    Args:
        demo: Existing Gradio Blocks/TabbedInterface instance

    Returns:
        Updated Gradio interface with workflow builder tab added
    """
    # This function should be called from multi_agent_team.py
    # to add the workflow builder as a new tab

    # Example integration:
    # with gr.Blocks() as enhanced_demo:
    #     with gr.Tabs():
    #         with gr.TabItem("Main Platform"):
    #             demo.render()
    #         with gr.TabItem("Visual Workflow Builder"):
    #             workflow_tab = create_workflow_builder_tab()
    #             workflow_tab.render()

    # return enhanced_demo

    pass  # Implementation depends on existing platform structure


# Example: Standalone usage
if __name__ == "__main__":
    import time

    print("=" * 60)
    print("  MULTI-AGENT VISUAL WORKFLOW BUILDER")
    print("=" * 60)
    print()

    # Start REST API server in background thread
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()
    print()

    # Start workflow builder React app
    if start_workflow_builder():
        print()
        print("Waiting for React dev server to start...")
        time.sleep(5)  # Give React time to start

        print()
        print("Services running:")
        print("  - React Workflow Builder: http://localhost:3000")
        print("  - REST API Server:        http://localhost:5000")
        print("  - Gradio Interface:       http://localhost:7860")
        print()
        print("Launching Gradio interface...")
        print()

        # Create and launch Gradio interface
        demo = create_standalone_interface()
        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            show_error=True
        )
    else:
        print()
        print("[ERROR] Failed to start workflow builder!")
        print("Please ensure Node.js and npm are installed.")
        print()
        print("Installation:")
        print("  1. Install Node.js: https://nodejs.org/")
        print("  2. cd workflow_builder")
        print("  3. npm install")
        print("  4. npm start")
