"""
Progress tracking system with 4 phases
Displays progress bars for: Planning, Drafting, Testing, Done
"""

import streamlit as st
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional


class ProgressPhase(Enum):
    """4 phases of execution"""
    PLANNING = ("Planning", "🔍")
    DRAFTING = ("Drafting", "✏️")
    TESTING = ("Testing", "🧪")
    DONE = ("Done", "✅")

    def __init__(self, label, emoji):
        self.label = label
        self.emoji = emoji


@dataclass
class PhaseProgress:
    """Progress for a single phase"""
    name: str
    progress: float  # 0.0 to 1.0
    status: str  # "pending", "active", "complete"
    emoji: str


class ProgressTracker:
    """Tracks progress across 4 phases with live updates"""

    def __init__(self):
        self.phases = {
            ProgressPhase.PLANNING: PhaseProgress("Planning", 0.0, "pending", "🔍"),
            ProgressPhase.DRAFTING: PhaseProgress("Drafting", 0.0, "pending", "✏️"),
            ProgressPhase.TESTING: PhaseProgress("Testing", 0.0, "pending", "🧪"),
            ProgressPhase.DONE: PhaseProgress("Done", 0.0, "pending", "✅")
        }
        self.current_phase = None
        self.progress_bars = {}
        self.container = None  # Main container for re-rendering

    def set_phase(self, phase: ProgressPhase):
        """Activate a specific phase"""
        # Mark previous phases as complete
        phase_order = list(ProgressPhase)
        current_index = phase_order.index(phase)

        for i, p in enumerate(phase_order):
            if i < current_index:
                self.phases[p].status = "complete"
                self.phases[p].progress = 1.0
            elif i == current_index:
                self.phases[p].status = "active"
                self.phases[p].progress = 0.0
            else:
                self.phases[p].status = "pending"
                self.phases[p].progress = 0.0

        self.current_phase = phase
        self._update_display()

    def update_phase_progress(self, progress: float):
        """Update progress for current phase (0.0 to 1.0)"""
        if self.current_phase:
            self.phases[self.current_phase].progress = max(0.0, min(1.0, progress))
            self._update_display()

    def render(self):
        """Initial render - create container"""
        if not self.container:
            self.container = st.empty()
        self._update_display()

    def _update_display(self):
        """Update display with current progress values"""
        if not self.container:
            return

        with self.container.container():
            for phase in ProgressPhase:
                phase_data = self.phases[phase]

                # Status indicator
                if phase_data.status == "complete":
                    status_emoji = "✅"
                    color = "🟢"
                elif phase_data.status == "active":
                    status_emoji = "🔄"
                    color = "🔵"
                else:
                    status_emoji = "⏸️"
                    color = "⚪"

                # Phase header with status
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{phase_data.emoji} {phase_data.name}**")
                with col2:
                    st.markdown(f"{color} {status_emoji}")

                # Progress bar
                st.progress(phase_data.progress)

                # Percentage
                st.caption(f"{int(phase_data.progress * 100)}%")
                st.markdown("<br>", unsafe_allow_html=True)
