"""
Report Generator: Export professional reports in PDF format

Generates two types of reports:
1. Executive Summary: High-level overview with charts, screenshots, recommendations
2. Dev Handover: Technical details with code diffs, Git commits, setup instructions
"""

import os
import io
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# PDF generation
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak,
    Table, TableStyle, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

# Charts
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image as PILImage


class ReportGenerator:
    """
    Generates professional PDF reports
    """

    def __init__(self):
        """Initialize report generator"""
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()

    def _create_custom_styles(self):
        """Create custom paragraph styles"""

        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Section header
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#3498DB'),
            spaceBefore=20,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        ))

        # Body text
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=11,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            leading=16
        ))

        # Highlight box
        self.styles.add(ParagraphStyle(
            name='HighlightBox',
            parent=self.styles['BodyText'],
            fontSize=11,
            textColor=colors.HexColor('#27AE60'),
            spaceBefore=10,
            spaceAfter=10,
            leftIndent=20,
            fontName='Helvetica-Bold'
        ))

    def generate_executive_summary(
        self,
        project_data: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        Generate Executive Summary PDF

        Args:
            project_data: Dict with project info, scores, screenshots, recommendations
            output_path: Where to save PDF

        Returns:
            Path to generated PDF
        """

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )

        story = []

        # Cover page
        story.extend(self._create_cover_page(project_data))
        story.append(PageBreak())

        # Executive Overview
        story.extend(self._create_overview_section(project_data))

        # Key Metrics
        if 'scores' in project_data:
            story.extend(self._create_metrics_section(project_data['scores']))

        # Funnel Analysis (if audit mode was used)
        if 'funnel_analysis' in project_data:
            story.extend(self._create_funnel_section(project_data['funnel_analysis']))

        # Screenshots
        if 'screenshots' in project_data and project_data['screenshots']:
            story.append(PageBreak())
            story.extend(self._create_screenshots_section(project_data['screenshots']))

        # Recommendations
        if 'recommendations' in project_data:
            story.append(PageBreak())
            story.extend(self._create_recommendations_section(project_data['recommendations']))

        # Build PDF
        doc.build(story)

        return output_path

    def generate_dev_handover(
        self,
        project_data: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        Generate Developer Handover PDF

        Args:
            project_data: Dict with technical details, diffs, setup instructions
            output_path: Where to save PDF

        Returns:
            Path to generated PDF
        """

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )

        story = []

        # Cover
        story.extend(self._create_dev_cover(project_data))
        story.append(PageBreak())

        # Tech Stack
        story.extend(self._create_tech_stack_section(project_data))

        # Project Structure
        if 'project_structure' in project_data:
            story.extend(self._create_structure_section(project_data['project_structure']))

        # Setup Instructions
        story.extend(self._create_setup_section(project_data))

        # Code Changes (if upgrade/audit)
        if 'code_diffs' in project_data:
            story.append(PageBreak())
            story.extend(self._create_diffs_section(project_data['code_diffs']))

        # Git Commits
        if 'git_commits' in project_data:
            story.extend(self._create_commits_section(project_data['git_commits']))

        # Testing Guide
        story.append(PageBreak())
        story.extend(self._create_testing_section(project_data))

        # Build PDF
        doc.build(story)

        return output_path

    def _create_cover_page(self, data: Dict) -> List:
        """Create executive summary cover page"""

        elements = []

        # Title
        title = data.get('project_name', 'Code Weaver Pro Report')
        elements.append(Paragraph(title, self.styles['CustomTitle']))
        elements.append(Spacer(1, 0.3*inch))

        # Subtitle
        subtitle = "Executive Summary"
        elements.append(Paragraph(
            f'<font size="16" color="#7F8C8D">{subtitle}</font>',
            self.styles['CustomBody']
        ))
        elements.append(Spacer(1, 0.5*inch))

        # Meta info
        meta_text = f"""
        <b>Generated:</b> {datetime.now().strftime('%B %d, %Y')}<br/>
        <b>Platform:</b> Code Weaver Pro<br/>
        <b>Status:</b> {data.get('status', 'Completed')}
        """
        elements.append(Paragraph(meta_text, self.styles['CustomBody']))

        return elements

    def _create_dev_cover(self, data: Dict) -> List:
        """Create dev handover cover page"""

        elements = []

        title = data.get('project_name', 'Project Documentation')
        elements.append(Paragraph(title, self.styles['CustomTitle']))
        elements.append(Spacer(1, 0.3*inch))

        subtitle = "Developer Handover"
        elements.append(Paragraph(
            f'<font size="16" color="#7F8C8D">{subtitle}</font>',
            self.styles['CustomBody']
        ))

        return elements

    def _create_overview_section(self, data: Dict) -> List:
        """Create overview section"""

        elements = []

        elements.append(Paragraph("Project Overview", self.styles['SectionHeader']))

        description = data.get('description', 'No description provided')
        elements.append(Paragraph(description, self.styles['CustomBody']))
        elements.append(Spacer(1, 0.2*inch))

        # Platforms
        platforms = data.get('platforms', [])
        if platforms:
            platforms_text = f"<b>Target Platforms:</b> {', '.join(platforms)}"
            elements.append(Paragraph(platforms_text, self.styles['CustomBody']))

        elements.append(Spacer(1, 0.3*inch))

        return elements

    def _create_metrics_section(self, scores: Dict) -> List:
        """Create metrics visualization section"""

        elements = []

        elements.append(Paragraph("Key Metrics", self.styles['SectionHeader']))

        # Create chart
        chart_path = self._generate_scores_chart(scores)
        if chart_path:
            img = Image(chart_path, width=5*inch, height=3*inch)
            elements.append(img)
            elements.append(Spacer(1, 0.2*inch))

            # Cleanup
            os.remove(chart_path)

        # Scores table
        score_data = [['Metric', 'Score', 'Rating']]
        for metric, score in scores.items():
            rating = self._score_to_rating(score)
            score_data.append([metric.replace('_', ' ').title(), f'{score}/10', rating])

        table = Table(score_data, colWidths=[2.5*inch, 1*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))

        return elements

    def _create_funnel_section(self, funnel_data: Dict) -> List:
        """Create funnel analysis section"""

        elements = []

        elements.append(Paragraph("User Funnel Analysis", self.styles['SectionHeader']))

        # Overall stats
        total = funnel_data.get('total_users', 0)
        completion = funnel_data.get('completion_rate', 0)

        stats_text = f"""
        <b>Total Users Analyzed:</b> {total}<br/>
        <b>Completion Rate:</b> {completion}%
        """
        elements.append(Paragraph(stats_text, self.styles['CustomBody']))
        elements.append(Spacer(1, 0.2*inch))

        # Funnel chart
        chart_path = self._generate_funnel_chart(funnel_data.get('funnel', {}))
        if chart_path:
            img = Image(chart_path, width=6*inch, height=3.5*inch)
            elements.append(img)
            elements.append(Spacer(1, 0.2*inch))
            os.remove(chart_path)

        # Biggest drop-off highlight
        biggest_drop = funnel_data.get('biggest_drop_off', {})
        if biggest_drop:
            drop_text = f"""
            <font size="13" color="#E74C3C"><b>Critical Issue:</b></font><br/>
            {biggest_drop['percentage']}% drop-off at <b>{biggest_drop['step']}</b>
            """
            elements.append(Paragraph(drop_text, self.styles['HighlightBox']))

        elements.append(Spacer(1, 0.3*inch))

        return elements

    def _create_screenshots_section(self, screenshots: List[str]) -> List:
        """Create screenshots gallery"""

        elements = []

        elements.append(Paragraph("Application Screenshots", self.styles['SectionHeader']))

        for i, screenshot_path in enumerate(screenshots[:4]):  # Max 4 screenshots
            if os.path.exists(screenshot_path):
                try:
                    img = Image(screenshot_path, width=5.5*inch, height=3.5*inch)
                    elements.append(img)
                    elements.append(Paragraph(
                        f'<font size="9" color="#7F8C8D">Screenshot {i+1}</font>',
                        self.styles['CustomBody']
                    ))
                    elements.append(Spacer(1, 0.3*inch))
                except Exception as e:
                    print(f"⚠️ Failed to add screenshot {screenshot_path}: {e}")

        return elements

    def _create_recommendations_section(self, recommendations: List[Dict]) -> List:
        """Create recommendations section"""

        elements = []

        elements.append(Paragraph("Recommendations", self.styles['SectionHeader']))

        for i, rec in enumerate(recommendations, 1):
            priority = rec.get('priority', 'medium')
            title = rec.get('title', 'Recommendation')
            description = rec.get('description', '')

            # Priority badge
            priority_colors = {
                'critical': '#E74C3C',
                'high': '#E67E22',
                'medium': '#F39C12',
                'low': '#95A5A6'
            }
            color = priority_colors.get(priority, '#95A5A6')

            rec_text = f"""
            <font size="12"><b>{i}. {title}</b></font>
            <font size="9" color="{color}"> [{priority.upper()}]</font><br/>
            {description}
            """
            elements.append(Paragraph(rec_text, self.styles['CustomBody']))

            # Suggestions
            if 'suggestions' in rec:
                for suggestion in rec['suggestions'][:3]:  # Top 3
                    elements.append(Paragraph(
                        f'  • {suggestion}',
                        self.styles['CustomBody']
                    ))

            elements.append(Spacer(1, 0.2*inch))

        return elements

    def _create_tech_stack_section(self, data: Dict) -> List:
        """Create tech stack section"""

        elements = []

        elements.append(Paragraph("Technology Stack", self.styles['SectionHeader']))

        tech_stack = data.get('tech_stack', {})

        for category, technologies in tech_stack.items():
            cat_text = f"<b>{category.replace('_', ' ').title()}:</b> {', '.join(technologies)}"
            elements.append(Paragraph(cat_text, self.styles['CustomBody']))

        elements.append(Spacer(1, 0.3*inch))

        return elements

    def _create_setup_section(self, data: Dict) -> List:
        """Create setup instructions"""

        elements = []

        elements.append(Paragraph("Setup Instructions", self.styles['SectionHeader']))

        setup_steps = data.get('setup_instructions', [
            'Clone the repository',
            'Install dependencies',
            'Configure environment variables',
            'Run development server'
        ])

        for i, step in enumerate(setup_steps, 1):
            elements.append(Paragraph(
                f'{i}. {step}',
                self.styles['CustomBody']
            ))

        elements.append(Spacer(1, 0.3*inch))

        return elements

    def _create_structure_section(self, structure: str) -> List:
        """Create project structure section"""

        elements = []

        elements.append(Paragraph("Project Structure", self.styles['SectionHeader']))

        # Format structure as code block
        structure_text = f'<font name="Courier" size="9">{structure}</font>'
        elements.append(Paragraph(structure_text, self.styles['CustomBody']))

        elements.append(Spacer(1, 0.3*inch))

        return elements

    def _create_diffs_section(self, diffs: List[Dict]) -> List:
        """Create code diffs section"""

        elements = []

        elements.append(Paragraph("Code Changes", self.styles['SectionHeader']))

        for diff in diffs[:5]:  # Top 5 diffs
            filename = diff.get('filename', 'unknown')
            changes = diff.get('changes', '')

            elements.append(Paragraph(
                f'<b>File:</b> {filename}',
                self.styles['CustomBody']
            ))

            # Truncate long diffs
            if len(changes) > 500:
                changes = changes[:500] + '\n... (truncated)'

            elements.append(Paragraph(
                f'<font name="Courier" size="8">{changes}</font>',
                self.styles['CustomBody']
            ))
            elements.append(Spacer(1, 0.2*inch))

        return elements

    def _create_commits_section(self, commits: List[str]) -> List:
        """Create Git commits section"""

        elements = []

        elements.append(Paragraph("Git Commits", self.styles['SectionHeader']))

        for commit in commits[:10]:  # Last 10 commits
            elements.append(Paragraph(
                f'  • {commit}',
                self.styles['CustomBody']
            ))

        elements.append(Spacer(1, 0.2*inch))

        return elements

    def _create_testing_section(self, data: Dict) -> List:
        """Create testing guide"""

        elements = []

        elements.append(Paragraph("Testing Guide", self.styles['SectionHeader']))

        test_results = data.get('test_results', [])

        if test_results:
            passed = sum(1 for t in test_results if t.get('passed', False))
            total = len(test_results)

            elements.append(Paragraph(
                f'<b>Tests Passed:</b> {passed}/{total}',
                self.styles['CustomBody']
            ))
        else:
            elements.append(Paragraph(
                'Run tests with: <font name="Courier">npm test</font> or <font name="Courier">pytest</font>',
                self.styles['CustomBody']
            ))

        elements.append(Spacer(1, 0.2*inch))

        return elements

    def _generate_scores_chart(self, scores: Dict) -> Optional[str]:
        """Generate bar chart for scores"""

        try:
            fig, ax = plt.subplots(figsize=(8, 4))

            metrics = [m.replace('_', ' ').title() for m in scores.keys()]
            values = list(scores.values())

            colors_list = ['#3498DB' if v >= 7 else '#F39C12' if v >= 5 else '#E74C3C' for v in values]

            ax.barh(metrics, values, color=colors_list)
            ax.set_xlabel('Score (0-10)', fontsize=12)
            ax.set_xlim(0, 10)
            ax.set_title('Application Metrics', fontsize=14, fontweight='bold')

            plt.tight_layout()

            # Save to temp file
            temp_path = f'/tmp/scores_chart_{datetime.now().timestamp()}.png'
            plt.savefig(temp_path, dpi=150, bbox_inches='tight')
            plt.close()

            return temp_path

        except Exception as e:
            print(f"⚠️ Chart generation failed: {e}")
            return None

    def _generate_funnel_chart(self, funnel_data: Dict) -> Optional[str]:
        """Generate funnel chart"""

        try:
            fig, ax = plt.subplots(figsize=(8, 5))

            steps = list(funnel_data.keys())
            percentages = [funnel_data[s]['percentage'] for s in steps]

            ax.barh(steps, percentages, color='#3498DB')
            ax.set_xlabel('Completion Rate (%)', fontsize=12)
            ax.set_xlim(0, 100)
            ax.set_title('User Journey Funnel', fontsize=14, fontweight='bold')

            for i, (step, pct) in enumerate(zip(steps, percentages)):
                ax.text(pct + 2, i, f'{pct}%', va='center', fontsize=10)

            plt.tight_layout()

            temp_path = f'/tmp/funnel_chart_{datetime.now().timestamp()}.png'
            plt.savefig(temp_path, dpi=150, bbox_inches='tight')
            plt.close()

            return temp_path

        except Exception as e:
            print(f"⚠️ Funnel chart failed: {e}")
            return None

    def _score_to_rating(self, score: float) -> str:
        """Convert numeric score to rating"""

        if score >= 8:
            return '⭐⭐⭐ Excellent'
        elif score >= 6:
            return '⭐⭐ Good'
        elif score >= 4:
            return '⭐ Fair'
        else:
            return '❌ Needs Work'


# Test function
def test_report_generator():
    """Test report generation"""

    generator = ReportGenerator()

    # Test data
    test_data = {
        'project_name': 'EV Charger Sharing Platform',
        'description': 'A platform where hosts list EV chargers and drivers book them.',
        'status': 'Completed',
        'platforms': ['Web App', 'iOS', 'Android'],
        'scores': {
            'speed': 8,
            'mobile_friendly': 7,
            'intuitiveness': 6,
            'functionality': 9
        },
        'funnel_analysis': {
            'total_users': 100,
            'completion_rate': 27,
            'funnel': {
                'landing': {'count': 100, 'percentage': 100},
                'signup_clicked': {'count': 85, 'percentage': 85},
                'form_filled': {'count': 45, 'percentage': 45},
                'form_submitted': {'count': 35, 'percentage': 35},
                'completed': {'count': 27, 'percentage': 27}
            },
            'biggest_drop_off': {
                'step': 'form_filled',
                'percentage': 47
            }
        },
        'recommendations': [
            {
                'priority': 'critical',
                'title': '47% drop-off at form_filled',
                'description': 'Major friction at form. Simplify immediately.',
                'suggestions': [
                    'Add progress indicator',
                    'Reduce required fields',
                    'Add social login options'
                ]
            }
        ]
    }

    # Generate executive summary
    exec_path = '/tmp/executive_summary_test.pdf'
    generator.generate_executive_summary(test_data, exec_path)
    print(f"Executive summary generated: {exec_path}")

    # Generate dev handover
    test_data['tech_stack'] = {
        'frontend': ['React', 'TypeScript', 'Tailwind CSS'],
        'backend': ['Node.js', 'Express', 'PostgreSQL']
    }
    test_data['setup_instructions'] = [
        'npm install',
        'cp .env.example .env',
        'npm run dev'
    ]

    dev_path = '/tmp/dev_handover_test.pdf'
    generator.generate_dev_handover(test_data, dev_path)
    print(f"Dev handover generated: {dev_path}")


if __name__ == "__main__":
    test_report_generator()
