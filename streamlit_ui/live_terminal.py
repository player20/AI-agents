import streamlit as st
from datetime import datetime
from collections import deque
from typing import Optional

class LiveTerminalOutput:
    """Terminal-style output display with color coding"""

    def __init__(self, max_lines: int = 100):
        """
        Initialize terminal output

        Args:
            max_lines: Maximum number of lines to keep in history
        """
        self.lines = deque(maxlen=max_lines)
        self.placeholder = None

    def add_line(self, line: str, level: str = "info") -> None:
        """
        Add a line to terminal output

        Args:
            line: The text to display
            level: "info", "success", "warning", "error"
        """
        # Sanitize user input to prevent security vulnerabilities
        line = str(line).strip()
        if not line:
            return

        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_line = {
            "timestamp": timestamp,
            "text": line,
            "level": level
        }
        self.lines.append(formatted_line)
        self.render()

    def clear(self) -> None:
        """Clear all terminal output"""
        self.lines.clear()
        self.render()

    def render(self) -> None:
        """Render terminal output with color coding"""
        if not self.placeholder:
            self.placeholder = st.empty()

        # Define colors based on level
        color_map = {
            "info": "#00ff00",      # Green
            "success": "#44ff44",   # Bright green
            "warning": "#ffff00",   # Accessible yellow
            "error": "#ff4444",     # Accessible red
            "system": "#00aaff"     # Blue
        }

        # Build HTML for terminal display
        terminal_html = "<div style='background-color: #1a1d29; border-radius: 8px; padding: 16px; font-family: \"Courier New\", monospace; height: 400px; overflow-y: auto; margin: 16px 0;'>"

        for line_data in self.lines:
            color = color_map.get(line_data["level"], "#00ff00")
            timestamp = line_data["timestamp"]
            text = line_data["text"]

            # HTML escape the text
            text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            terminal_html += f"<div style='color: {color}; margin-bottom: 4px;'>[{timestamp}] {text}</div>"

        terminal_html += "</div>"

        self.placeholder.markdown(terminal_html, unsafe_allow_html=True)

    def add_success(self, message: str) -> None:
        """Add a success message"""
        self.add_line(f"✓ {message}", "success")

    def add_error(self, message: str) -> None:
        """Add an error message"""
        self.add_line(f"✗ {message}", "error")

    def add_warning(self, message: str) -> None:
        """Add a warning message"""
        self.add_line(f"⚠ {message}", "warning")

    def add_info(self, message: str) -> None:
        """Add an info message"""
        self.add_line(f"• {message}", "info")

    def add_system(self, message: str) -> None:
        """Add a system message"""
        self.add_line(f"[SYSTEM] {message}", "system")

def create_terminal() -> LiveTerminalOutput:
    """Factory function to create a new terminal instance"""
    return LiveTerminalOutput()