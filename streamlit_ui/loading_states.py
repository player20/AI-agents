"""
Loading States and Skeleton Screens

Provides visual feedback during loading operations with skeleton loaders
and animated placeholders for a polished UX.
"""

import streamlit as st


def inject_loading_css():
    """Inject CSS for loading animations."""
    st.markdown("""
    <style>
    /* Skeleton loading animation */
    @keyframes shimmer {
        0% {
            background-position: -200px 0;
        }
        100% {
            background-position: 200px 0;
        }
    }

    @keyframes pulse-glow {
        0%, 100% {
            opacity: 1;
            box-shadow: 0 0 10px rgba(102, 126, 234, 0.3);
        }
        50% {
            opacity: 0.7;
            box-shadow: 0 0 20px rgba(102, 126, 234, 0.6);
        }
    }

    .skeleton {
        background: linear-gradient(
            90deg,
            rgba(30, 33, 57, 0.8) 0%,
            rgba(50, 55, 90, 0.8) 50%,
            rgba(30, 33, 57, 0.8) 100%
        );
        background-size: 400px 100%;
        animation: shimmer 1.5s ease-in-out infinite;
        border-radius: 8px;
    }

    .skeleton-text {
        height: 16px;
        margin: 8px 0;
    }

    .skeleton-title {
        height: 24px;
        width: 60%;
        margin: 12px 0;
    }

    .skeleton-card {
        padding: 20px;
        background: linear-gradient(135deg, #1e2139 0%, #252844 100%);
        border: 2px solid #3d4466;
        border-radius: 16px;
        margin: 12px 0;
    }

    .skeleton-metric {
        height: 48px;
        width: 100%;
        margin: 8px 0;
    }

    .skeleton-progress {
        height: 8px;
        width: 100%;
        border-radius: 4px;
        margin: 16px 0;
    }

    /* Loading spinner */
    .loading-spinner {
        display: inline-block;
position: relative;
        width: 40px;
        height: 40px;
        border: 4px solid rgba(102, 126, 234, 0.2);
        border-radius: 50%;
        border-top-color: #667eea;
        animation: spin 1s ease-in-out infinite;
    }
.loading-spinner::after {
        content: "Loading...";
        position: absolute;
        top: 55px;
        left: 50%;
        transform: translateX(-50%);
        color: #CBD5E1;
        font-size: 16px;
        font-weight: 500;
        animation: pulse-glow 2s ease-in-out infinite;
    }

    @keyframes spin {
        to {
            transform: rotate(360deg);
        }
    }

    /* Pulsing dot for active phases */
    .pulse-dot {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #667eea;
        animation: pulse-glow 1.5s ease-in-out infinite;
    }

    /* Loading overlay */
    .loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(10, 14, 39, 0.85);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 9999;
    }

    .loading-text {
        color: #e8eaf6;
        margin-top: 16px;
        font-size: 18px;
        font-weight: 500;
    }

    /* Progress bar enhancement */
    .enhanced-progress {
        background: rgba(102, 126, 234, 0.1);
        border-radius: 8px;
        height: 12px;
        overflow: hidden;
        position: relative;
    }

    .enhanced-progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 8px;
        transition: width 0.3s ease;
    }

    .enhanced-progress-glow {
        position: absolute;
        top: 0;
        right: 0;
        bottom: 0;
        width: 50px;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3));
        animation: progress-glow 2s ease-in-out infinite;
    }

    @keyframes progress-glow {
        0%, 100% { opacity: 0; }
        50% { opacity: 1; }
    }
    </style>
    """, unsafe_allow_html=True)


def render_skeleton_card(title: bool = True, lines: int = 3, metrics: int = 0):
    """
    Render a skeleton loading card.

    Args:
        title: Whether to show a title skeleton
        lines: Number of text line skeletons
        metrics: Number of metric skeletons
    """
    html = '<div class="skeleton-card">'

    if title:
        html += '<div class="skeleton skeleton-title"></div>'

    for _ in range(lines):
        html += '<div class="skeleton skeleton-text"></div>'

    if metrics > 0:
        html += '<div style="display: flex; gap: 16px; margin-top: 12px;">'
        for _ in range(metrics):
            html += '<div class="skeleton skeleton-metric" style="flex: 1;"></div>'
        html += '</div>'

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_skeleton_results():
    """Render skeleton loading state for results section."""
    inject_loading_css()

    st.markdown("""
    <div style="text-align: center; margin: 20px 0;">
        <div class="loading-spinner"></div>
        <p class="loading-text">Generating your results...</p>
    </div>
    """, unsafe_allow_html=True)

    # Skeleton for scores
    st.markdown('<div style="display: flex; gap: 16px;">', unsafe_allow_html=True)
    for _ in range(4):
        st.markdown("""
        <div style="flex: 1;">
            <div class="skeleton skeleton-metric"></div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Skeleton for content
    render_skeleton_card(title=True, lines=4, metrics=0)
    render_skeleton_card(title=True, lines=3, metrics=0)


def render_loading_spinner(message: str = "Loading..."):
    """Render a centered loading spinner with message."""
    inject_loading_css()

    st.markdown(f"""
    <div style="text-align: center; padding: 40px;">
        <div class="loading-spinner"></div>
        <p class="loading-text">{message}</p>
    </div>
    """, unsafe_allow_html=True)


def render_progress_enhanced(progress: float, label: str = ""):
    """
    Render an enhanced progress bar with glow effect.

    Args:
        progress: Progress value from 0.0 to 1.0
        label: Optional label text
    """
    inject_loading_css()

    percentage = int(progress * 100)
    st.markdown(f"""
    <div style="margin: 16px 0;">
        {f'<p style="color: #CBD5E1; margin-bottom: 8px;">{label}</p>' if label else ''}
        <div class="enhanced-progress">
            <div class="enhanced-progress-fill" style="width: {percentage}%;"></div>
            <div class="enhanced-progress-glow"></div>
        </div>
        <p style="color: #667eea; text-align: right; font-size: 14px; margin-top: 4px;">{percentage}%</p>
    </div>
    """, unsafe_allow_html=True)


def render_phase_indicator(phases: list, current_phase: int):
    """
    Render phase indicator with active phase highlighted.

    Args:
        phases: List of phase names
        current_phase: Index of current phase (0-based)
    """
    inject_loading_css()

    html = '<div style="display: flex; justify-content: center; gap: 24px; margin: 20px 0;">'

    for i, phase in enumerate(phases):
        if i < current_phase:
            # Completed
            status_html = '<span style="color: #10b981; margin-right: 8px;">&#10003;</span>'
            text_style = 'color: #10b981;'
        elif i == current_phase:
            # Active
            status_html = '<span class="pulse-dot" style="margin-right: 8px;"></span>'
            text_style = 'color: #667eea; font-weight: 600;'
        else:
            # Pending
            status_html = '<span style="color: #6b7280; margin-right: 8px;">&#9675;</span>'
            text_style = 'color: #6b7280;'

        html += f'''
        <div style="display: flex; align-items: center; {text_style}">
            {status_html}
            {phase}
        </div>
        '''

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


# Issue #9 - Form submission and success feedback functions

def render_form_submission_loading(message: str = "Processing your request..."):
    """
    Show loading state during form submission with overlay effect.

    Args:
        message: Loading message to display
    """
    inject_loading_css()

    st.markdown(f"""
    <div style="
        background: rgba(10, 14, 39, 0.95);
        border-radius: 16px;
        padding: 40px;
        text-align: center;
        border: 1px solid rgba(102, 126, 234, 0.3);
        margin: 20px 0;
    ">
        <div class="loading-spinner" style="margin: 0 auto;"></div>
        <p class="loading-text" style="margin-top: 20px; font-size: 18px;">{message}</p>
        <p style="color: #CBD5E1; font-size: 14px; margin-top: 8px;">
            This may take a moment
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_success_confirmation(message: str = "Success!", description: str = None):
    """
    Show success confirmation with animation.

    Args:
        message: Success message to display
        description: Optional description text
    """
    inject_loading_css()

    st.markdown("""
    <style>
    @keyframes success-pop {
        0% { transform: scale(0); opacity: 0; }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); opacity: 1; }
    }
    .success-container {
        animation: success-pop 0.5s ease-out;
    }
    </style>
    """, unsafe_allow_html=True)

    desc_html = f'<p style="color: #CBD5E1; font-size: 14px; margin-top: 8px;">{description}</p>' if description else ''

    st.markdown(f"""
    <div class="success-container" style="
        text-align: center;
        padding: 32px;
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 16px;
        margin: 20px 0;
    ">
        <div style="font-size: 48px; margin-bottom: 16px;">&#10003;</div>
        <div style="
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 12px 24px;
            border-radius: 12px;
            font-weight: 600;
            display: inline-block;
            font-size: 18px;
        ">{message}</div>
        {desc_html}
    </div>
    """, unsafe_allow_html=True)


def render_error_state(message: str = "Something went wrong", description: str = None, retry_callback=None):
    """
    Show error state with retry option.

    Args:
        message: Error message to display
        description: Optional description text
        retry_callback: Optional callback function for retry button
    """
    inject_loading_css()

    desc_html = f'<p style="color: #CBD5E1; font-size: 14px; margin-top: 8px;">{description}</p>' if description else ''

    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 32px;
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.1) 100%);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 16px;
        margin: 20px 0;
    ">
        <div style="font-size: 48px; margin-bottom: 16px;">&#10060;</div>
        <div style="
            color: #ef4444;
            font-weight: 600;
            font-size: 18px;
            margin-bottom: 8px;
        ">{message}</div>
        {desc_html}
    </div>
    """, unsafe_allow_html=True)

    if retry_callback:
        if st.button("Try Again", type="primary", use_container_width=True):
            retry_callback()


# =============================================================================
# FORM PROGRESS & VALIDATION COMPONENTS
# =============================================================================

def render_form_progress(steps: list, current_step: int = 0, show_percentage: bool = True):
    """
    Render a form progress indicator showing completion status with constructive messaging.

    Args:
        steps: List of step names (e.g., ["Basic Info", "Details", "Review"])
        current_step: Current step index (0-based)
        show_percentage: Whether to show percentage complete
    """
    inject_loading_css()

    total = len(steps)
    completed = min(current_step, total)
    percentage = int((completed / total) * 100) if total > 0 else 0

    # Constructive progress message instead of bare percentage
    if completed == 0:
        progress_text = "Start with your idea below"
    elif completed == total:
        progress_text = "All sections complete! ✓"
    else:
        progress_text = f"Section {completed + 1} of {total}: {steps[min(completed, len(steps)-1)]}"

    percent_html = f'<span style="color: #10B981; font-weight: 700;">{progress_text}</span>' if show_percentage else ''

    st.markdown(f"""
    <div class="form-progress" role="progressbar" aria-valuenow="{percentage}" aria-valuemin="0" aria-valuemax="100" aria-label="Form completion progress">
        <div class="form-progress-header">
            <span class="form-progress-label">Your Progress</span>
            {percent_html}
        </div>
        <div class="form-progress-bar">
            <div class="form-progress-fill" style="width: {max(percentage, 5)}%;"></div>
        </div>
        <div class="form-progress-steps" role="list">
    """, unsafe_allow_html=True)

    # Step indicators
    for i, step in enumerate(steps):
        if i < current_step:
            status_class = "complete"
            icon = "✓"
        elif i == current_step:
            status_class = "active"
            icon = "●"
        else:
            status_class = ""
            icon = "○"

        st.markdown(f"""
            <div class="form-step {status_class}" role="listitem">
                <span class="form-step-dot"></span>
                <span>{step}</span>
            </div>
        """, unsafe_allow_html=True)

    st.markdown('</div></div>', unsafe_allow_html=True)


def render_character_counter(current: int, min_chars: int = 0, max_chars: int = 500, optimal_min: int = 50):
    """
    Render a character counter with constructive visual feedback.

    Args:
        current: Current character count
        min_chars: Minimum required characters
        max_chars: Maximum allowed characters
        optimal_min: Minimum for optimal input quality
    """
    if current >= optimal_min and current <= max_chars:
        status_class = "good"
        status_text = "Great! Ready to go"
        icon = "✓"
    elif current < min_chars:
        status_class = "info"  # Use info/amber instead of harsh red
        status_text = f"{min_chars} characters minimum for best results"
        icon = "ℹ️"
    elif current > max_chars:
        status_class = "limit"
        status_text = f"{current - max_chars} characters over limit"
        icon = "⚠️"
    elif current < optimal_min:
        status_class = "info"  # Use info/amber instead of warning
        status_text = f"Add {optimal_min - current} more for better AI results"
        icon = "💡"
    else:
        status_class = ""
        status_text = ""
        icon = ""

    st.markdown(f"""
    <div class="char-counter {status_class}" role="status" aria-live="polite">
        {icon} {current}/{max_chars} characters {f'• {status_text}' if status_text else ''}
    </div>
    """, unsafe_allow_html=True)


def render_required_label(label: str, required: bool = True, helper_text: str = None):
    """
    Render a field label with required indicator and optional helper text.

    Args:
        label: The label text
        required: Whether the field is required
        helper_text: Optional helper text below the label
    """
    required_html = '<span class="required-indicator" aria-label="required">*</span>' if required else ''
    helper_html = f'<p class="field-helper">{helper_text}</p>' if helper_text else ''

    st.markdown(f"""
    <label class="field-label">
        {label}{required_html}
    </label>
    {helper_html}
    """, unsafe_allow_html=True)


def render_field_validation(is_valid: bool, error_message: str = None, success_message: str = None):
    """
    Render field validation feedback.

    Args:
        is_valid: Whether the field is valid
        error_message: Message to show on error
        success_message: Message to show on success
    """
    if is_valid and success_message:
        st.markdown(f"""
        <div class="success-message" role="status" aria-live="polite">
            {success_message}
        </div>
        """, unsafe_allow_html=True)
    elif not is_valid and error_message:
        st.markdown(f"""
        <div class="error-message" role="alert" aria-live="assertive">
            {error_message}
        </div>
        """, unsafe_allow_html=True)


def render_section_header(title: str, description: str = None, completion_status: str = None):
    """
    Render a form section header with optional description and status.

    Args:
        title: Section title
        description: Optional description text
        completion_status: Optional status like "Complete", "In Progress", etc.
    """
    status_html = ""
    if completion_status:
        if completion_status.lower() == "complete":
            status_html = '<span style="color: #34d399; font-size: 14px; margin-left: 12px;">✓ Complete</span>'
        elif completion_status.lower() == "in progress":
            status_html = '<span style="color: #667eea; font-size: 14px; margin-left: 12px;">● In Progress</span>'
        else:
            status_html = f'<span style="color: #CBD5E1; font-size: 14px; margin-left: 12px;">{completion_status}</span>'

    desc_html = f'<p style="color: #CBD5E1; font-size: 14px; margin-top: 8px;">{description}</p>' if description else ''

    st.markdown(f"""
    <div class="section-header" role="heading" aria-level="2">
        {title}{status_html}
    </div>
    {desc_html}
    """, unsafe_allow_html=True)


# =============================================================================
# GENERATION LOADING OVERLAY
# =============================================================================

def render_generation_overlay(
    current_step: int = 0,
    total_steps: int = 5,
    step_name: str = "Analyzing your idea...",
    show_tips: bool = True
):
    """
    Render a full-page generation loading overlay with progress and engaging tips.

    Args:
        current_step: Current step number (0-based)
        total_steps: Total number of steps
        step_name: Name of the current step being executed
        show_tips: Whether to show rotating tips
    """
    inject_loading_css()

    percentage = int(((current_step + 1) / total_steps) * 100)

    # Step names for visual progress
    default_steps = [
        ("🧠", "Analyzing Idea"),
        ("📊", "Market Research"),
        ("🎨", "Designing UX"),
        ("⚙️", "Building Features"),
        ("📝", "Creating Proposal")
    ]

    # Build step indicators
    steps_html = ""
    for i, (icon, name) in enumerate(default_steps[:total_steps]):
        if i < current_step:
            status_class = "gen-step-complete"
            status_icon = "✓"
        elif i == current_step:
            status_class = "gen-step-active"
            status_icon = icon
        else:
            status_class = "gen-step-pending"
            status_icon = icon

        steps_html += f'''
        <div class="gen-step {status_class}">
            <span class="gen-step-icon">{status_icon}</span>
            <span class="gen-step-name">{name}</span>
        </div>
        '''

    # Tips that rotate
    tips_html = ""
    if show_tips:
        tips_html = '''
        <div class="gen-tip" id="generation-tip">
            <span class="gen-tip-icon">💡</span>
            <span class="gen-tip-text">AI agents are collaborating on your project...</span>
        </div>
        <script>
            (function() {
                const tips = [
                    "AI agents are collaborating on your project...",
                    "Analyzing market trends and competitors...",
                    "Designing user-friendly interfaces...",
                    "Optimizing for your target audience...",
                    "Creating professional documentation...",
                    "Preparing your client-ready proposal..."
                ];
                let tipIndex = 0;
                const tipElement = document.querySelector('#generation-tip .gen-tip-text');
                if (tipElement) {
                    setInterval(function() {
                        tipIndex = (tipIndex + 1) % tips.length;
                        tipElement.style.opacity = '0';
                        setTimeout(function() {
                            tipElement.textContent = tips[tipIndex];
                            tipElement.style.opacity = '1';
                        }, 300);
                    }, 4000);
                }
            })();
        </script>
        '''

    st.markdown(f"""
    <style>
    /* Generation overlay styles */
    .gen-overlay {{
        background: linear-gradient(135deg, rgba(10, 14, 39, 0.98) 0%, rgba(30, 33, 57, 0.98) 100%);
        border-radius: 24px;
        padding: 48px 32px;
        margin: 40px auto;
        max-width: 600px;
        text-align: center;
        border: 1px solid rgba(102, 126, 234, 0.3);
        box-shadow: 0 24px 80px rgba(0, 0, 0, 0.5);
    }}

    .gen-spinner {{
        width: 64px;
        height: 64px;
        border: 4px solid rgba(102, 126, 234, 0.2);
        border-radius: 50%;
        border-top-color: #667eea;
        border-right-color: #764ba2;
        animation: gen-spin 1s ease-in-out infinite;
        margin: 0 auto 24px;
    }}

    @keyframes gen-spin {{
        to {{ transform: rotate(360deg); }}
    }}

    .gen-title {{
        font-size: 24px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 8px;
    }}

    .gen-step-name-active {{
        font-size: 18px;
        color: #CBD5E1;
        margin-bottom: 32px;
    }}

    .gen-progress-container {{
        background: rgba(102, 126, 234, 0.1);
        border-radius: 12px;
        height: 12px;
        overflow: hidden;
        margin-bottom: 24px;
    }}

    .gen-progress-fill {{
        height: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #10B981 100%);
        border-radius: 12px;
        transition: width 0.5s ease;
        background-size: 200% 100%;
        animation: gen-progress-shimmer 2s linear infinite;
    }}

    @keyframes gen-progress-shimmer {{
        0% {{ background-position: 200% 0; }}
        100% {{ background-position: -200% 0; }}
    }}

    .gen-steps {{
        display: flex;
        justify-content: space-between;
        margin-bottom: 32px;
        padding: 0 8px;
    }}

    .gen-step {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
        flex: 1;
    }}

    .gen-step-icon {{
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        background: rgba(102, 126, 234, 0.1);
        border: 2px solid rgba(102, 126, 234, 0.3);
        transition: all 0.3s ease;
    }}

    .gen-step-complete .gen-step-icon {{
        background: rgba(16, 185, 129, 0.2);
        border-color: #10B981;
        color: #10B981;
    }}

    .gen-step-active .gen-step-icon {{
        background: rgba(102, 126, 234, 0.3);
        border-color: #667eea;
        box-shadow: 0 0 20px rgba(102, 126, 234, 0.5);
        animation: gen-pulse 1.5s ease-in-out infinite;
    }}

    @keyframes gen-pulse {{
        0%, 100% {{ transform: scale(1); }}
        50% {{ transform: scale(1.1); }}
    }}

    .gen-step-pending .gen-step-icon {{
        opacity: 0.5;
    }}

    .gen-step-name {{
        font-size: 11px;
        color: #6b7280;
        font-weight: 500;
    }}

    .gen-step-complete .gen-step-name {{
        color: #10B981;
    }}

    .gen-step-active .gen-step-name {{
        color: #667eea;
        font-weight: 600;
    }}

    .gen-tip {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        padding: 12px 20px;
        background: rgba(102, 126, 234, 0.1);
        border-radius: 12px;
        margin-top: 24px;
    }}

    .gen-tip-icon {{
        font-size: 20px;
    }}

    .gen-tip-text {{
        font-size: 14px;
        color: #CBD5E1;
        transition: opacity 0.3s ease;
    }}

    /* Mobile adjustments */
    @media (max-width: 767px) {{
        .gen-overlay {{
            padding: 32px 20px;
            margin: 20px 12px;
        }}

        .gen-steps {{
            flex-wrap: wrap;
            gap: 16px;
        }}

        .gen-step {{
            flex: 0 0 calc(33% - 12px);
        }}

        .gen-step-name {{
            font-size: 10px;
        }}
    }}
    </style>

    <div class="gen-overlay" role="status" aria-live="polite" aria-label="Generation in progress">
        <div class="gen-spinner"></div>
        <div class="gen-title">Creating Your App</div>
        <div class="gen-step-name-active">{step_name}</div>

        <div class="gen-progress-container">
            <div class="gen-progress-fill" style="width: {percentage}%;"></div>
        </div>

        <div class="gen-steps">
            {steps_html}
        </div>

        {tips_html}
    </div>
    """, unsafe_allow_html=True)


def render_empty_state(
    icon: str = "📂",
    title: str = "Nothing here yet",
    description: str = "Upload files or start a new project to get started.",
    action_text: str = None,
    action_icon: str = "→"
):
    """
    Render an empty state with guidance for users.

    Args:
        icon: Main icon to display
        title: Title text
        description: Description/guidance text
        action_text: Optional action hint text
        action_icon: Icon for the action hint
    """
    inject_loading_css()

    action_html = ""
    if action_text:
        action_html = f'''
        <div class="empty-state-action">
            <span>{action_icon}</span>
            <span>{action_text}</span>
        </div>
        '''

    st.markdown(f"""
    <style>
    .empty-state {{
        text-align: center;
        padding: 48px 32px;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(139, 92, 246, 0.05) 100%);
        border: 2px dashed rgba(102, 126, 234, 0.25);
        border-radius: 16px;
        margin: 24px 0;
    }}

    .empty-state-icon {{
        font-size: 56px;
        margin-bottom: 16px;
        opacity: 0.8;
    }}

    .empty-state-title {{
        font-size: 20px;
        font-weight: 600;
        color: #e8eaf6;
        margin-bottom: 8px;
    }}

    .empty-state-description {{
        font-size: 15px;
        color: #9CA3AF;
        max-width: 400px;
        margin: 0 auto 16px;
        line-height: 1.6;
    }}

    .empty-state-action {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 10px 20px;
        background: rgba(102, 126, 234, 0.15);
        border-radius: 20px;
        color: #667eea;
        font-size: 14px;
        font-weight: 500;
        margin-top: 8px;
    }}
    </style>

    <div class="empty-state" role="status">
        <div class="empty-state-icon">{icon}</div>
        <div class="empty-state-title">{title}</div>
        <div class="empty-state-description">{description}</div>
        {action_html}
    </div>
    """, unsafe_allow_html=True)


def render_generation_complete(project_name: str = "Your App", proposal_ready: bool = True):
    """
    Render a completion celebration when generation finishes.

    Args:
        project_name: Name of the project/app that was generated
        proposal_ready: Whether a proposal document was generated
    """
    inject_loading_css()

    proposal_html = ""
    if proposal_ready:
        proposal_html = '''
        <div class="gen-complete-item">
            <span class="gen-complete-icon">📝</span>
            <span>Client-ready proposal generated</span>
        </div>
        '''

    st.markdown(f"""
    <style>
    @keyframes gen-celebrate {{
        0% {{ transform: scale(0) rotate(-180deg); opacity: 0; }}
        50% {{ transform: scale(1.2) rotate(10deg); }}
        100% {{ transform: scale(1) rotate(0deg); opacity: 1; }}
    }}

    .gen-complete {{
        text-align: center;
        padding: 48px 32px;
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 24px;
        margin: 40px auto;
        max-width: 600px;
        animation: gen-celebrate 0.6s ease-out;
    }}

    .gen-complete-badge {{
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 40px;
        margin: 0 auto 24px;
        box-shadow: 0 8px 32px rgba(16, 185, 129, 0.4);
    }}

    .gen-complete-title {{
        font-size: 28px;
        font-weight: 700;
        color: #10B981;
        margin-bottom: 8px;
    }}

    .gen-complete-subtitle {{
        font-size: 18px;
        color: #CBD5E1;
        margin-bottom: 24px;
    }}

    .gen-complete-items {{
        display: flex;
        flex-direction: column;
        gap: 12px;
        margin-bottom: 24px;
    }}

    .gen-complete-item {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        color: #e8eaf6;
        font-size: 15px;
    }}

    .gen-complete-icon {{
        font-size: 20px;
    }}
    </style>

    <div class="gen-complete" role="status" aria-live="polite">
        <div class="gen-complete-badge">✓</div>
        <div class="gen-complete-title">Generation Complete!</div>
        <div class="gen-complete-subtitle">{project_name} is ready</div>

        <div class="gen-complete-items">
            <div class="gen-complete-item">
                <span class="gen-complete-icon">✨</span>
                <span>All features analyzed and designed</span>
            </div>
            <div class="gen-complete-item">
                <span class="gen-complete-icon">📊</span>
                <span>Market research completed</span>
            </div>
            {proposal_html}
        </div>
    </div>
    """, unsafe_allow_html=True)
