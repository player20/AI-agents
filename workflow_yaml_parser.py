"""
Workflow YAML Parser
Parses YAML workflow files exported from the Workflow Builder
and converts them to Gradio Platform configuration
"""

import yaml
import re
from typing import Dict, List, Any, Tuple


def parse_workflow_yaml(file_path: str) -> Dict[str, Any]:
    """
    Parse YAML workflow file exported from Workflow Builder

    Args:
        file_path: Path to YAML workflow file

    Returns:
        Dictionary containing parsed workflow configuration:
        {
            'name': str,
            'agents': List[str],  # Agent IDs
            'custom_prompts': Dict[str, str],  # agent_id -> prompt
            'models': Dict[str, str],  # agent_id -> model_id
            'priorities': Dict[str, int],  # agent_id -> priority
            'custom_agents': List[Dict],  # Custom agent definitions
            'connections': List[Dict],  # Agent connections
            'metadata': Dict  # Additional metadata
        }
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            workflow_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML file: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error reading file: {str(e)}")

    # Validate required fields
    if not workflow_data:
        raise ValueError("YAML file is empty")

    if not isinstance(workflow_data, dict):
        raise ValueError("YAML file must contain a dictionary")

    # Extract workflow metadata
    workflow_name = workflow_data.get('name', 'Untitled Workflow')
    workflow_name = sanitize_text(workflow_name)

    # Extract agents
    agents = workflow_data.get('agents', [])
    if not agents:
        raise ValueError("Workflow must contain at least one agent")

    # Extract connections
    connections = workflow_data.get('connections', [])

    # Extract custom agents
    custom_agents = workflow_data.get('custom_agents', [])

    # Parse agent configurations
    agent_ids = []
    custom_prompts = {}
    agent_models = {}

    for agent in agents:
        if not isinstance(agent, dict):
            continue

        agent_type = agent.get('type', '').strip()
        if not agent_type:
            continue

        agent_ids.append(agent_type)

        # Extract custom prompt if provided
        if 'prompt' in agent and agent['prompt']:
            custom_prompts[agent_type] = sanitize_text(agent['prompt'])

        # Extract model if specified
        if 'model' in agent and agent['model']:
            agent_models[agent_type] = agent['model']

    # Calculate execution priority from connections
    priority_map = calculate_priority_from_connections(agent_ids, connections)

    # Build result
    result = {
        'name': workflow_name,
        'agents': agent_ids,
        'custom_prompts': custom_prompts,
        'models': agent_models,
        'priorities': priority_map,
        'custom_agents': custom_agents,
        'connections': connections,
        'metadata': {
            'agent_count': len(agent_ids),
            'connection_count': len(connections),
            'custom_agent_count': len(custom_agents),
            'has_custom_prompts': len(custom_prompts) > 0,
            'has_model_overrides': len(agent_models) > 0
        }
    }

    return result


def calculate_priority_from_connections(agent_ids: List[str], connections: List[Dict]) -> Dict[str, int]:
    """
    Calculate execution priority based on connection dependencies
    Uses topological sort to determine execution order

    Args:
        agent_ids: List of agent IDs in workflow
        connections: List of connections between agents

    Returns:
        Dictionary mapping agent_id to priority (1-20)
    """
    # Build adjacency list (dependencies)
    dependencies = {agent_id: set() for agent_id in agent_ids}

    for conn in connections:
        source = conn.get('source', '')
        target = conn.get('target', '')

        # Extract node ID from connection (format: "PM-12345" -> "PM")
        source_id = extract_agent_id_from_node(source)
        target_id = extract_agent_id_from_node(target)

        if source_id in dependencies and target_id in dependencies:
            # Target depends on source (source must run first)
            dependencies[target_id].add(source_id)

    # Topological sort to determine priority
    priority_map = {}
    visited = set()
    priority = 1

    # Process agents with no dependencies first
    while len(visited) < len(agent_ids):
        # Find agents with all dependencies satisfied
        ready = [
            agent_id for agent_id in agent_ids
            if agent_id not in visited and dependencies[agent_id].issubset(visited)
        ]

        if not ready:
            # Circular dependency detected or isolated agents
            # Assign remaining agents same priority
            remaining = [aid for aid in agent_ids if aid not in visited]
            for agent_id in remaining:
                priority_map[agent_id] = priority
            break

        # Assign same priority to all ready agents (can run in parallel)
        for agent_id in ready:
            priority_map[agent_id] = priority
            visited.add(agent_id)

        priority += 1

    return priority_map


def extract_agent_id_from_node(node_id: str) -> str:
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


def sanitize_text(text: str, max_length: int = 10000) -> str:
    """
    Sanitize text input to prevent injection attacks and encoding issues

    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]

    # Remove control characters but keep newlines and tabs
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)

    # Remove potentially harmful sequences
    text = text.replace('\x00', '')  # Null bytes

    return text.strip()


def validate_workflow(workflow_data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """
    Validate imported workflow for errors and warnings

    Args:
        workflow_data: Parsed workflow data

    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    errors = []
    warnings = []

    # Check required fields
    if 'name' not in workflow_data or not workflow_data['name']:
        errors.append("Missing workflow name")

    if 'agents' not in workflow_data or len(workflow_data['agents']) == 0:
        errors.append("Workflow must contain at least one agent")

    # Check for empty agent IDs
    for agent_id in workflow_data.get('agents', []):
        if not agent_id or not agent_id.strip():
            errors.append("Found agent with empty ID")

    # Check for custom agents
    if workflow_data.get('custom_agents'):
        custom_count = len(workflow_data['custom_agents'])
        warnings.append(
            f"Workflow contains {custom_count} custom agent(s). "
            "These may not be available in the Gradio Platform."
        )

    # Check for circular dependencies
    connections = workflow_data.get('connections', [])
    if connections:
        cycles = detect_circular_dependencies(workflow_data['agents'], connections)
        if cycles:
            warnings.append(f"Circular dependencies detected: {' → '.join(cycles[0])}")

    # Check for disconnected agents
    if connections:
        disconnected = find_disconnected_agents(workflow_data['agents'], connections)
        if disconnected:
            warnings.append(
                f"Disconnected agents (no connections): {', '.join(disconnected)}"
            )

    # Validate models
    for agent_id, model in workflow_data.get('models', {}).items():
        if not model or not isinstance(model, str):
            warnings.append(f"Invalid model for agent {agent_id}: {model}")

    is_valid = len(errors) == 0
    return is_valid, errors, warnings


def detect_circular_dependencies(agent_ids: List[str], connections: List[Dict]) -> List[List[str]]:
    """
    Detect circular dependencies in workflow connections using DFS

    Args:
        agent_ids: List of agent IDs
        connections: List of connections

    Returns:
        List of cycles found (each cycle is a list of agent IDs)
    """
    # Build adjacency list
    graph = {agent_id: [] for agent_id in agent_ids}

    for conn in connections:
        source = extract_agent_id_from_node(conn.get('source', ''))
        target = extract_agent_id_from_node(conn.get('target', ''))

        if source in graph and target in graph:
            graph[source].append(target)

    # DFS to detect cycles
    cycles = []
    visited = set()
    rec_stack = set()

    def dfs(node, path):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor, path.copy()):
                    return True
            elif neighbor in rec_stack:
                # Found cycle
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                cycles.append(cycle)
                return True

        rec_stack.remove(node)
        return False

    for agent_id in agent_ids:
        if agent_id not in visited:
            dfs(agent_id, [])

    return cycles


def find_disconnected_agents(agent_ids: List[str], connections: List[Dict]) -> List[str]:
    """
    Find agents with no incoming or outgoing connections

    Args:
        agent_ids: List of agent IDs
        connections: List of connections

    Returns:
        List of disconnected agent IDs
    """
    connected = set()

    for conn in connections:
        source = extract_agent_id_from_node(conn.get('source', ''))
        target = extract_agent_id_from_node(conn.get('target', ''))
        connected.add(source)
        connected.add(target)

    disconnected = [agent_id for agent_id in agent_ids if agent_id not in connected]
    return disconnected


def format_import_summary(workflow_data: Dict[str, Any]) -> str:
    """
    Format a human-readable import summary

    Args:
        workflow_data: Parsed workflow data

    Returns:
        Formatted summary string
    """
    metadata = workflow_data.get('metadata', {})

    summary = f"✅ Successfully imported: {workflow_data['name']}\n\n"
    summary += f"📊 Workflow Statistics:\n"
    summary += f"  • Agents: {metadata.get('agent_count', 0)}\n"
    summary += f"  • Connections: {metadata.get('connection_count', 0)}\n"

    if metadata.get('custom_agent_count', 0) > 0:
        summary += f"  • Custom Agents: {metadata['custom_agent_count']}\n"

    if metadata.get('has_custom_prompts'):
        prompt_count = len(workflow_data.get('custom_prompts', {}))
        summary += f"  • Custom Prompts: {prompt_count}\n"

    if metadata.get('has_model_overrides'):
        model_count = len(workflow_data.get('models', {}))
        summary += f"  • Model Overrides: {model_count}\n"

    return summary


# Example usage and testing
if __name__ == "__main__":
    # Test with sample workflow
    sample_yaml = """
name: Test Workflow
agents:
  - type: PM
    prompt: "Custom PM prompt"
    model: claude-3-sonnet-20240229
  - type: Research
    prompt: ""
    model: claude-3-haiku-20240307
  - type: Ideas
connections:
  - source: PM-123
    target: Research-456
  - source: Research-456
    target: Ideas-789
"""

    # Write sample to temp file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        f.write(sample_yaml)
        temp_path = f.name

    try:
        # Parse workflow
        result = parse_workflow_yaml(temp_path)
        print("Parsed workflow:")
        print(f"  Name: {result['name']}")
        print(f"  Agents: {result['agents']}")
        print(f"  Priorities: {result['priorities']}")
        print(f"  Custom Prompts: {result['custom_prompts']}")
        print(f"  Models: {result['models']}")

        # Validate
        valid, errors, warnings = validate_workflow(result)
        print(f"\nValidation: {'VALID' if valid else 'INVALID'}")
        if errors:
            print(f"Errors: {errors}")
        if warnings:
            print(f"Warnings: {warnings}")

        # Format summary
        summary = format_import_summary(result)
        print(f"\nSummary generated successfully (emojis may not display in console)")

    finally:
        import os
        os.unlink(temp_path)
