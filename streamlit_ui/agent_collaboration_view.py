"""
Real-Time Agent Collaboration View

Provides a visual representation of agents working together in real-time.
Shows agent status, messages, and collaboration flow for transparency.
"""

import streamlit as st
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import time


class AgentStatus(Enum):
    """Status of an agent in the workflow."""
    IDLE = "idle"
    THINKING = "thinking"
    WORKING = "working"
    COMPLETED = "completed"
    ERROR = "error"
    WAITING = "waiting"


@dataclass
class AgentActivity:
    """Represents an agent's activity in the collaboration."""
    agent_id: str
    agent_name: str
    agent_role: str
    status: AgentStatus = AgentStatus.IDLE
    current_task: str = ""
    messages: List[Dict[str, Any]] = field(default_factory=list)
    progress: float = 0.0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    output_preview: str = ""


class AgentCollaborationView:
    """
    Renders a real-time view of agents collaborating on a task.

    Features:
    - Visual agent cards with status indicators
    - Message flow between agents
    - Progress tracking
    - Live updates during execution
    """

    # Agent role icons
    AGENT_ICONS = {
        'MetaPrompt': '🎯',
        'Research': '📊',
        'Challenger': '🤔',
        'PM': '📋',
        'Ideas': '💡',
        'Designs': '🎨',
        'Senior': '👨‍💻',
        'Reflector': '🔄',
        'Web': '🌐',
        'iOS': '📱',
        'Android': '🤖',
        'Verifier': '✅',
        'default': '🤖'
    }

    # Status colors
    STATUS_COLORS = {
        AgentStatus.IDLE: '#6b7280',      # Gray
        AgentStatus.THINKING: '#f59e0b',   # Amber
        AgentStatus.WORKING: '#3b82f6',    # Blue
        AgentStatus.COMPLETED: '#10b981',  # Green
        AgentStatus.ERROR: '#ef4444',      # Red
        AgentStatus.WAITING: '#8b5cf6',    # Purple
    }

    # Status animations
    STATUS_ANIMATIONS = {
        AgentStatus.THINKING: 'pulse',
        AgentStatus.WORKING: 'bounce',
        AgentStatus.WAITING: 'pulse',
    }

    def __init__(self):
        """Initialize the collaboration view."""
        if 'agent_activities' not in st.session_state:
            st.session_state.agent_activities = {}
        if 'collaboration_messages' not in st.session_state:
            st.session_state.collaboration_messages = []
        if 'collaboration_started' not in st.session_state:
            st.session_state.collaboration_started = None

    def initialize_agents(self, agent_configs: List[Dict[str, str]]):
        """
        Initialize agents for the collaboration view.

        Args:
            agent_configs: List of agent configurations with id, name, role
        """
        st.session_state.agent_activities = {}
        for config in agent_configs:
            agent_id = config.get('id', config.get('name', 'unknown'))
            st.session_state.agent_activities[agent_id] = AgentActivity(
                agent_id=agent_id,
                agent_name=config.get('name', agent_id),
                agent_role=config.get('role', 'Agent')
            )
        st.session_state.collaboration_messages = []
        st.session_state.collaboration_started = datetime.now().isoformat()

    def update_agent_status(self, agent_id: str, status: AgentStatus,
                           task: str = "", progress: float = 0.0):
        """
        Update an agent's status.

        Args:
            agent_id: Agent identifier
            status: New status
            task: Current task description
            progress: Progress percentage (0-1)
        """
        if agent_id in st.session_state.agent_activities:
            activity = st.session_state.agent_activities[agent_id]
            activity.status = status
            activity.current_task = task
            activity.progress = progress

            if status == AgentStatus.WORKING and not activity.started_at:
                activity.started_at = datetime.now().isoformat()
            elif status == AgentStatus.COMPLETED:
                activity.completed_at = datetime.now().isoformat()

    def add_agent_message(self, from_agent: str, to_agent: Optional[str],
                         message: str, message_type: str = "info"):
        """
        Add a message to the collaboration flow.

        Args:
            from_agent: Sending agent ID
            to_agent: Receiving agent ID (None for broadcast)
            message: Message content
            message_type: Type of message (info, handoff, result, error)
        """
        st.session_state.collaboration_messages.append({
            'from': from_agent,
            'to': to_agent,
            'message': message,
            'type': message_type,
            'timestamp': datetime.now().isoformat()
        })

        # Add to agent's messages
        if from_agent in st.session_state.agent_activities:
            st.session_state.agent_activities[from_agent].messages.append({
                'direction': 'out',
                'to': to_agent,
                'message': message,
                'type': message_type
            })

    def set_agent_output(self, agent_id: str, output: str):
        """Set the output preview for an agent."""
        if agent_id in st.session_state.agent_activities:
            # Truncate long outputs
            st.session_state.agent_activities[agent_id].output_preview = output[:500] + "..." if len(output) > 500 else output

    def render(self, show_messages: bool = True, compact: bool = False):
        """
        Render the collaboration view.

        Args:
            show_messages: Whether to show the message flow
            compact: Whether to use compact layout
        """
        self._inject_css()

        st.markdown("""
        <div class="collab-header" role="region" aria-labelledby="collab-heading">
            <h3 id="collab-heading">🤝 Agent Collaboration</h3>
            <p>Watch your AI team work together in real-time</p>
        </div>
        <div id="collab-live-region" aria-live="polite" aria-atomic="false" class="sr-only">
            <!-- Screen reader announcements for progress updates -->
        </div>
        """, unsafe_allow_html=True)

        # Agent cards grid
        if compact:
            self._render_compact_view()
        else:
            self._render_full_view()

        # Message flow
        if show_messages and st.session_state.collaboration_messages:
            self._render_message_flow()

    def _render_full_view(self):
        """Render full agent cards view."""
        activities = list(st.session_state.agent_activities.values())

        if not activities:
            st.info("No agents initialized yet. Start a task to see collaboration.")
            return

        # Create rows of 4 agents
        for i in range(0, len(activities), 4):
            row_activities = activities[i:i+4]
            cols = st.columns(len(row_activities))

            for col, activity in zip(cols, row_activities):
                with col:
                    self._render_agent_card(activity)

    def _render_compact_view(self):
        """Render compact inline view."""
        activities = list(st.session_state.agent_activities.values())

        if not activities:
            return

        # Single row with status indicators
        html = '<div class="collab-compact">'
        for activity in activities:
            icon = self.AGENT_ICONS.get(activity.agent_id, self.AGENT_ICONS['default'])
            color = self.STATUS_COLORS.get(activity.status, '#6b7280')
            animation = self.STATUS_ANIMATIONS.get(activity.status, '')
            anim_class = f'status-{animation}' if animation else ''

            html += f'''
            <div class="compact-agent {anim_class}" title="{activity.agent_name}: {activity.current_task or 'Idle'}">
                <span class="compact-icon">{icon}</span>
                <span class="compact-dot" style="background: {color};"></span>
            </div>
            '''
        html += '</div>'

        st.markdown(html, unsafe_allow_html=True)

    def _render_agent_card(self, activity: AgentActivity):
        """Render a single agent card."""
        icon = self.AGENT_ICONS.get(activity.agent_id, self.AGENT_ICONS['default'])
        color = self.STATUS_COLORS.get(activity.status, '#6b7280')
        animation = self.STATUS_ANIMATIONS.get(activity.status, '')
        anim_class = f'status-{animation}' if animation else ''

        status_text = activity.status.value.title()
        if activity.status == AgentStatus.WORKING:
            status_text = f"Working ({int(activity.progress * 100)}%)"

        progress_bar = f'<div class="agent-progress" role="progressbar" aria-valuenow="{int(activity.progress * 100)}" aria-valuemin="0" aria-valuemax="100" aria-label="{activity.agent_name} progress"><div class="progress-fill" style="width: {activity.progress * 100}%; background: {color};"></div></div>' if activity.progress > 0 else ''

        card_html = f'''
        <div class="agent-card {anim_class}" style="border-color: {color};" role="article" aria-labelledby="agent-{activity.agent_id}">
            <div class="agent-header">
                <span class="agent-icon" aria-hidden="true">{icon}</span>
                <div class="agent-info">
                    <div class="agent-name" id="agent-{activity.agent_id}">{activity.agent_name}</div>
                    <div class="agent-role">{activity.agent_role}</div>
                </div>
                <div class="status-badge" style="background: {color};" role="status" aria-live="polite">
                    {status_text}
                </div>
            </div>
            <div class="agent-task" aria-label="Current task">{activity.current_task or "Waiting for task..."}</div>
            {progress_bar}
        </div>
        '''
        st.markdown(card_html, unsafe_allow_html=True)

    def _render_message_flow(self):
        """Render the message flow between agents."""
        messages = st.session_state.collaboration_messages[-10:]  # Last 10 messages

        if not messages:
            return

        with st.expander("📨 Agent Communication Log", expanded=False):
            for msg in reversed(messages):
                from_icon = self.AGENT_ICONS.get(msg['from'], '🤖')
                to_icon = self.AGENT_ICONS.get(msg['to'], '📢') if msg['to'] else '📢'

                type_colors = {
                    'info': '#3b82f6',
                    'handoff': '#8b5cf6',
                    'result': '#10b981',
                    'error': '#ef4444'
                }
                color = type_colors.get(msg['type'], '#6b7280')

                st.markdown(f"""
                <div class="message-item" style="border-left-color: {color};">
                    <span class="msg-from">{from_icon} {msg['from']}</span>
                    <span class="msg-arrow">→</span>
                    <span class="msg-to">{to_icon} {msg['to'] or 'All'}</span>
                    <div class="msg-content">{msg['message'][:100]}{'...' if len(msg['message']) > 100 else ''}</div>
                </div>
                """, unsafe_allow_html=True)

    def _inject_css(self):
        """Inject CSS styles for the collaboration view."""
        st.markdown("""
        <style>
        .collab-header {
            text-align: center;
            margin-bottom: 24px;
        }
        .collab-header h3 {
            color: #e8eaf6;
            margin-bottom: 4px;
        }
        .collab-header p {
            color: #9ca3af;
            font-size: 14px;
        }

        .agent-card {
            background: linear-gradient(135deg, #1e2139 0%, #252844 100%);
            border: 2px solid #3d4466;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            transition: all 0.3s ease;
        }

        .agent-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }

        .agent-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
        }

        .agent-icon {
            font-size: 28px;
        }

        .agent-info {
            flex: 1;
        }

        .agent-name {
            font-weight: 600;
            color: #e8eaf6;
            font-size: 14px;
        }

        .agent-role {
            font-size: 11px;
            color: #9ca3af;
        }

        .status-badge {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: 600;
            color: white;
            text-transform: uppercase;
        }

        .agent-task {
            font-size: 12px;
            color: #9ca3af;
            padding: 8px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
            min-height: 40px;
        }

        .agent-progress {
            height: 4px;
            background: rgba(255,255,255,0.1);
            border-radius: 2px;
            margin-top: 8px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            border-radius: 2px;
            transition: width 0.3s ease;
        }

        /* Animations */
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }

        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-4px); }
        }

        .status-pulse {
            animation: pulse 1.5s ease-in-out infinite;
        }

        .status-bounce {
            animation: bounce 1s ease-in-out infinite;
        }

        /* Compact view */
        .collab-compact {
            display: flex;
            gap: 8px;
            padding: 12px;
            background: rgba(30, 33, 57, 0.5);
            border-radius: 12px;
            justify-content: center;
            flex-wrap: wrap;
        }

        .compact-agent {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 8px;
            cursor: pointer;
        }

        .compact-icon {
            font-size: 24px;
        }

        .compact-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-top: 4px;
        }

        /* Message flow */
        .message-item {
            padding: 8px 12px;
            margin: 8px 0;
            background: rgba(30, 33, 57, 0.5);
            border-radius: 8px;
            border-left: 3px solid;
        }

        .msg-from, .msg-to {
            font-size: 12px;
            font-weight: 600;
            color: #e8eaf6;
        }

        .msg-arrow {
            color: #6b7280;
            margin: 0 8px;
        }

        .msg-content {
            font-size: 12px;
            color: #9ca3af;
            margin-top: 4px;
        }
        </style>
        """, unsafe_allow_html=True)


def render_agent_collaboration(agents: List[Dict] = None, compact: bool = False):
    """
    Convenience function to render agent collaboration view.

    Args:
        agents: Optional list of agent configs to initialize
        compact: Whether to use compact layout
    """
    view = AgentCollaborationView()

    if agents:
        view.initialize_agents(agents)

    view.render(compact=compact)
    return view


# Example usage for testing
if __name__ == "__main__":
    st.set_page_config(page_title="Agent Collaboration Demo", layout="wide")

    # Initialize with sample agents
    sample_agents = [
        {'id': 'MetaPrompt', 'name': 'Meta Prompt', 'role': 'Idea Expander'},
        {'id': 'Research', 'name': 'Researcher', 'role': 'Market Analyst'},
        {'id': 'PM', 'name': 'Product Manager', 'role': 'Requirements'},
        {'id': 'Designs', 'name': 'Designer', 'role': 'UI/UX'},
        {'id': 'Senior', 'name': 'Senior Dev', 'role': 'Architecture'},
        {'id': 'Web', 'name': 'Web Dev', 'role': 'Implementation'},
    ]

    view = AgentCollaborationView()
    view.initialize_agents(sample_agents)

    # Simulate some activity
    view.update_agent_status('MetaPrompt', AgentStatus.COMPLETED, 'Expanded user idea', 1.0)
    view.update_agent_status('Research', AgentStatus.COMPLETED, 'Market analysis done', 1.0)
    view.update_agent_status('PM', AgentStatus.WORKING, 'Writing requirements...', 0.6)
    view.update_agent_status('Designs', AgentStatus.THINKING, 'Analyzing requirements...')
    view.update_agent_status('Senior', AgentStatus.WAITING, 'Waiting for designs')
    view.update_agent_status('Web', AgentStatus.IDLE)

    view.add_agent_message('MetaPrompt', 'Research', 'Here is the expanded project spec', 'handoff')
    view.add_agent_message('Research', 'PM', 'Market looks promising, GO decision', 'result')
    view.add_agent_message('PM', None, 'Starting requirements gathering', 'info')

    view.render(show_messages=True)
