"""
Workflow Visualization Module
Generates visual workflow diagrams using Graphviz
Displays agent connections and execution status
"""

try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False
    print("⚠️  Graphviz not available. Install with: pip install graphviz")
    print("    Also install Graphviz system binaries from: https://graphviz.org/download/")


def generate_workflow_graph(workflow_data, execution_status=None):
    """
    Generate workflow visualization using Graphviz

    Args:
        workflow_data: Parsed workflow from YAML (dict with 'agents', 'connections', etc.)
        execution_status: Optional dict of agent_id -> status ("pending", "running", "completed", "failed")

    Returns:
        SVG string for embedding in Gradio HTML component, or error message if Graphviz unavailable
    """
    if not GRAPHVIZ_AVAILABLE:
        return "<div style='padding: 20px; text-align: center; color: #666;'>⚠️ Graphviz not installed. Install with: pip install graphviz</div>"

    try:
        # Create directed graph
        dot = graphviz.Digraph(
            comment='Workflow Visualization',
            format='svg',
            engine='dot'
        )

        # Graph attributes for modern look
        dot.attr(
            rankdir='LR',  # Left to right layout
            bgcolor='transparent',
            splines='ortho',  # Orthogonal edges
            nodesep='0.8',
            ranksep='1.2'
        )

        # Default node attributes
        dot.attr('node',
            shape='box',
            style='rounded,filled',
            fontname='Inter, sans-serif',
            fontsize='14',
            margin='0.3,0.2'
        )

        # Default edge attributes
        dot.attr('edge',
            color='#9CA3AF',
            penwidth='2',
            arrowsize='0.8'
        )

        # Agent icon mapping (matches workflow builder)
        agent_icons = {
            'PM': '📋',
            'Memory': '🧠',
            'Research': '🔍',
            'Ideas': '💡',
            'Designs': '🎨',
            'Senior': '👨‍💻',
            'iOS': '📱',
            'Android': '🤖',
            'Web': '🌐',
            'QA': '✅',
            'Verifier': '🔎',
            'DevOps': '🔧',
            'Security': '🔒',
            'DataArchitect': '📊',
            'Marketing': '📢',
            'Legal': '⚖️'
        }

        # Add nodes (agents)
        agents = workflow_data.get('agents', [])
        if not agents:
            return "<div style='padding: 20px; text-align: center; color: #666;'>No agents in workflow</div>"

        for agent_id in agents:
            # Get execution status
            status = 'pending'
            if execution_status and agent_id in execution_status:
                status = execution_status[agent_id]

            # Get agent icon
            icon = agent_icons.get(agent_id, '⚙️')

            # Node styling based on status
            if status == 'running':
                fillcolor = '#F59E0B'  # Orange
                fontcolor = 'white'
                penwidth = '3'
                style = 'rounded,filled,bold'
            elif status == 'completed':
                fillcolor = '#10B981'  # Green
                fontcolor = 'white'
                penwidth = '2'
                style = 'rounded,filled'
            elif status == 'failed':
                fillcolor = '#EF4444'  # Red
                fontcolor = 'white'
                penwidth = '2'
                style = 'rounded,filled'
            else:  # pending
                fillcolor = '#E5E7EB'  # Light gray
                fontcolor = '#374151'  # Dark gray text
                penwidth = '2'
                style = 'rounded,filled'

            # Create node label with icon and name
            label = f"{icon} {agent_id}"

            dot.node(
                agent_id,
                label=label,
                fillcolor=fillcolor,
                fontcolor=fontcolor,
                penwidth=penwidth,
                style=style
            )

        # Add edges (connections)
        connections = workflow_data.get('connections', [])
        if connections:
            for conn in connections:
                source_node = conn.get('source', '')
                target_node = conn.get('target', '')

                # Extract agent ID from node ID (format: "PM-12345" -> "PM")
                source_id = extract_agent_id_from_node(source_node)
                target_id = extract_agent_id_from_node(target_node)

                # Only add edge if both agents exist
                if source_id in agents and target_id in agents:
                    dot.edge(source_id, target_id)

        # Render to SVG
        svg_data = dot.pipe(format='svg').decode('utf-8')

        # Wrap SVG in styled container
        html_output = f"""
        <div style="
            background: white;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 24px;
            margin: 16px 0;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        ">
            <h3 style="
                margin: 0 0 16px 0;
                font-size: 18px;
                font-weight: 600;
                color: #1F2937;
            ">📊 Workflow Visualization</h3>
            <div style="overflow-x: auto;">
                {svg_data}
            </div>
        </div>
        """

        return html_output

    except Exception as e:
        error_msg = f"Error generating workflow visualization: {str(e)}"
        return f"<div style='padding: 20px; color: #EF4444;'>⚠️ {error_msg}</div>"


def extract_agent_id_from_node(node_id):
    """
    Extract agent type ID from node ID
    Node IDs have format: "AgentType-timestamp" (e.g., "PM-1234567890")

    Args:
        node_id: Full node ID from workflow

    Returns:
        Agent type ID (e.g., "PM")
    """
    if not node_id:
        return ""

    # Split on dash and take first part
    parts = node_id.split('-')
    if len(parts) >= 1:
        return parts[0]

    return node_id


def generate_execution_status_legend():
    """
    Generate HTML legend for workflow execution status

    Returns:
        HTML string with status legend
    """
    legend_html = """
    <div style="
        display: flex;
        gap: 16px;
        padding: 12px 16px;
        background: #F9FAFB;
        border-radius: 8px;
        margin: 8px 0;
        font-size: 14px;
    ">
        <div style="display: flex; align-items: center; gap: 6px;">
            <div style="width: 12px; height: 12px; background: #E5E7EB; border-radius: 3px;"></div>
            <span>Pending</span>
        </div>
        <div style="display: flex; align-items: center; gap: 6px;">
            <div style="width: 12px; height: 12px; background: #F59E0B; border-radius: 3px;"></div>
            <span>Running</span>
        </div>
        <div style="display: flex; align-items: center; gap: 6px;">
            <div style="width: 12px; height: 12px; background: #10B981; border-radius: 3px;"></div>
            <span>Completed</span>
        </div>
        <div style="display: flex; align-items: center; gap: 6px;">
            <div style="width: 12px; height: 12px; background: #EF4444; border-radius: 3px;"></div>
            <span>Failed</span>
        </div>
    </div>
    """
    return legend_html


# Example usage and testing
if __name__ == "__main__":
    # Test with sample workflow data
    sample_workflow = {
        'name': 'Test Workflow',
        'agents': ['PM', 'Research', 'Ideas', 'Designs', 'Senior'],
        'connections': [
            {'source': 'PM-123', 'target': 'Research-456'},
            {'source': 'Research-456', 'target': 'Ideas-789'},
            {'source': 'Ideas-789', 'target': 'Designs-101'},
            {'source': 'Designs-101', 'target': 'Senior-202'}
        ]
    }

    # Test with different execution statuses
    execution_statuses = [
        {},  # All pending
        {'PM': 'completed', 'Research': 'running'},  # Partially executed
        {'PM': 'completed', 'Research': 'completed', 'Ideas': 'failed'}  # With failure
    ]

    for i, status in enumerate(execution_statuses):
        print(f"\n=== Test {i+1}: {list(status.keys()) if status else 'All pending'} ===")
        result = generate_workflow_graph(sample_workflow, status)
        if GRAPHVIZ_AVAILABLE:
            print(f"Generated SVG of length: {len(result)} characters")
        else:
            print(result)

    # Test legend
    print("\n=== Status Legend ===")
    legend = generate_execution_status_legend()
    print(f"Generated legend of length: {len(legend)} characters")
