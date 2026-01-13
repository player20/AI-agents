"""
A/B Test Generator: Creates variants for testing different approaches

Generates 2-3 variants of screens/flows with different:
- Color schemes
- Layouts
- Copy/messaging
- CTAs (calls-to-action)

Outputs deployable branches with analytics tracking for each variant
"""

import os
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import git
from datetime import datetime


class ABTestGenerator:
    """
    Generates A/B test variants for screens and flows
    """

    def __init__(self, project_path: str):
        """
        Initialize with project path

        Args:
            project_path: Path to generated project
        """
        self.project_path = Path(project_path)

    def generate_variants(
        self,
        variant_count: int = 3,
        variant_dimensions: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate A/B test variants

        Args:
            variant_count: Number of variants to generate (2-3)
            variant_dimensions: Dimensions to vary (color, layout, copy, cta)

        Returns:
            List of variant metadata with branch names
        """

        if variant_dimensions is None:
            variant_dimensions = ['color', 'copy', 'cta']

        variants = []

        # Define variant configurations
        variant_configs = [
            {
                'id': 'control',
                'name': 'Control (Original)',
                'description': 'Original design - baseline',
                'changes': {}
            },
            {
                'id': 'variant_a',
                'name': 'Variant A: Bold & Action-Oriented',
                'description': 'Vibrant colors, action-oriented copy, prominent CTAs',
                'changes': {
                    'color': {
                        'primary': '#FF5722',  # Bold orange
                        'secondary': '#FFC107',  # Amber
                        'accent': '#4CAF50'  # Green
                    },
                    'copy': {
                        'style': 'action-oriented',
                        'tone': 'urgent',
                        'length': 'short'
                    },
                    'cta': {
                        'size': 'large',
                        'text': ['Get Started Now', 'Join Free', 'Start Today'],
                        'placement': 'prominent'
                    }
                }
            },
            {
                'id': 'variant_b',
                'name': 'Variant B: Trust & Calm',
                'description': 'Professional colors, trust-building copy, softer CTAs',
                'changes': {
                    'color': {
                        'primary': '#3F51B5',  # Professional blue
                        'secondary': '#9C27B0',  # Purple
                        'accent': '#00BCD4'  # Cyan
                    },
                    'copy': {
                        'style': 'trust-building',
                        'tone': 'professional',
                        'length': 'medium'
                    },
                    'cta': {
                        'size': 'medium',
                        'text': ['Learn More', 'See How It Works', 'Explore Features'],
                        'placement': 'balanced'
                    }
                }
            }
        ]

        # Generate only requested number of variants
        for i, config in enumerate(variant_configs[:variant_count]):
            variant = self._create_variant(config, variant_dimensions)
            variants.append(variant)

        return variants

    def _create_variant(
        self,
        config: Dict[str, Any],
        dimensions: List[str]
    ) -> Dict[str, Any]:
        """
        Create a single variant with code changes

        Args:
            config: Variant configuration
            dimensions: Which dimensions to apply

        Returns:
            Variant metadata
        """

        variant_id = config['id']
        changes = config.get('changes', {})

        # Build file modifications
        file_modifications = []

        if 'color' in dimensions and 'color' in changes:
            file_modifications.extend(
                self._generate_color_changes(changes['color'])
            )

        if 'copy' in dimensions and 'copy' in changes:
            file_modifications.extend(
                self._generate_copy_changes(changes['copy'])
            )

        if 'cta' in dimensions and 'cta' in changes:
            file_modifications.extend(
                self._generate_cta_changes(changes['cta'])
            )

        return {
            'id': variant_id,
            'name': config['name'],
            'description': config['description'],
            'branch_name': f'ab-test/{variant_id}',
            'changes': changes,
            'file_modifications': file_modifications,
            'tracking_events': self._generate_tracking_events(variant_id),
            'metrics_to_track': [
                'conversion_rate',
                'bounce_rate',
                'time_on_page',
                'cta_clicks',
                'signup_completions'
            ]
        }

    def _generate_color_changes(self, color_config: Dict[str, str]) -> List[Dict]:
        """Generate CSS/style changes for colors"""

        modifications = []

        # CSS variable changes
        css_changes = f"""
/* A/B Test Variant Colors */
:root {{
  --color-primary: {color_config['primary']};
  --color-secondary: {color_config['secondary']};
  --color-accent: {color_config['accent']};
}}

.btn-primary {{
  background-color: {color_config['primary']};
}}

.btn-secondary {{
  background-color: {color_config['secondary']};
}}

.accent {{
  color: {color_config['accent']};
}}
"""

        modifications.append({
            'file_pattern': '**/*.css',
            'type': 'append',
            'content': css_changes,
            'description': 'Updated color scheme'
        })

        # For React/Tailwind projects
        tailwind_config = f"""
// A/B Test Variant Colors
module.exports = {{
  theme: {{
    extend: {{
      colors: {{
        primary: '{color_config['primary']}',
        secondary: '{color_config['secondary']}',
        accent: '{color_config['accent']}',
      }}
    }}
  }}
}}
"""

        modifications.append({
            'file_pattern': 'tailwind.config.js',
            'type': 'replace',
            'content': tailwind_config,
            'description': 'Updated Tailwind color config'
        })

        return modifications

    def _generate_copy_changes(self, copy_config: Dict[str, str]) -> List[Dict]:
        """Generate copy/text changes"""

        modifications = []

        # Copy suggestions based on style
        style = copy_config.get('style', 'neutral')

        copy_patterns = {
            'action-oriented': {
                'headlines': [
                    'Start Building Today',
                    'Transform Your Workflow Now',
                    'Get Results in Minutes'
                ],
                'subheadlines': [
                    'Join thousands of users already saving time',
                    'No credit card required. Start free.',
                    'Setup in under 2 minutes'
                ]
            },
            'trust-building': {
                'headlines': [
                    'Built for Professionals',
                    'Trusted by Leading Companies',
                    'Enterprise-Grade Security'
                ],
                'subheadlines': [
                    'See why teams choose us for mission-critical work',
                    'Compliant with industry standards',
                    'Backed by 24/7 expert support'
                ]
            }
        }

        if style in copy_patterns:
            modifications.append({
                'file_pattern': '**/landing/**',
                'type': 'suggest',
                'suggestions': copy_patterns[style],
                'description': f'Copy suggestions for {style} tone'
            })

        return modifications

    def _generate_cta_changes(self, cta_config: Dict[str, Any]) -> List[Dict]:
        """Generate CTA button changes"""

        modifications = []

        size = cta_config.get('size', 'medium')
        texts = cta_config.get('text', [])

        # Button size CSS
        size_styles = {
            'small': 'padding: 8px 16px; font-size: 14px;',
            'medium': 'padding: 12px 24px; font-size: 16px;',
            'large': 'padding: 16px 32px; font-size: 18px; font-weight: bold;'
        }

        cta_css = f"""
/* A/B Test CTA Styles */
.cta-button {{
  {size_styles[size]}
  border-radius: 8px;
  transition: all 0.3s ease;
}}

.cta-button:hover {{
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}}
"""

        modifications.append({
            'file_pattern': '**/*.css',
            'type': 'append',
            'content': cta_css,
            'description': f'Updated CTA button size to {size}'
        })

        # CTA text suggestions
        if texts:
            modifications.append({
                'file_pattern': '**/components/**',
                'type': 'suggest',
                'suggestions': {'cta_texts': texts},
                'description': 'Alternative CTA button texts'
            })

        return modifications

    def _generate_tracking_events(self, variant_id: str) -> Dict[str, str]:
        """
        Generate analytics tracking events for variant

        Returns:
            Dict of event names -> implementation snippets
        """

        return {
            'page_view': f"""
// Track variant page view
posthog.capture('ab_test_page_view', {{
  variant: '{variant_id}',
  timestamp: new Date().toISOString()
}});
""",
            'cta_click': f"""
// Track CTA click
posthog.capture('ab_test_cta_clicked', {{
  variant: '{variant_id}',
  button_text: event.target.innerText,
  timestamp: new Date().toISOString()
}});
""",
            'signup_completed': f"""
// Track signup completion
posthog.capture('ab_test_signup_completed', {{
  variant: '{variant_id}',
  timestamp: new Date().toISOString()
}});
"""
        }

    def create_variant_branches(
        self,
        variants: List[Dict[str, Any]],
        base_branch: str = 'main'
    ) -> List[str]:
        """
        Create Git branches for each variant

        Args:
            variants: List of variant metadata
            base_branch: Base branch to branch from

        Returns:
            List of created branch names
        """

        created_branches = []

        try:
            repo = git.Repo(self.project_path)

            for variant in variants:
                if variant['id'] == 'control':
                    # Control stays on base branch
                    created_branches.append(base_branch)
                    continue

                branch_name = variant['branch_name']

                # Create new branch
                try:
                    # Checkout base branch first
                    repo.git.checkout(base_branch)

                    # Create and checkout new branch
                    new_branch = repo.create_head(branch_name)
                    new_branch.checkout()

                    # Apply modifications would go here
                    # (In real implementation, apply file_modifications)

                    # Commit variant changes
                    repo.index.add('*')
                    repo.index.commit(f'A/B Test: {variant["name"]}\n\n{variant["description"]}')

                    created_branches.append(branch_name)

                except Exception as e:
                    print(f"⚠️ Failed to create branch {branch_name}: {e}")
                    continue

            # Return to base branch
            repo.git.checkout(base_branch)

        except Exception as e:
            print(f"⚠️ Git operation failed: {e}")

        return created_branches

    def generate_experiment_config(
        self,
        variants: List[Dict[str, Any]],
        traffic_split: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Generate experiment configuration for analytics platform

        Args:
            variants: List of variants
            traffic_split: Custom traffic split (default: equal split)

        Returns:
            Experiment config for PostHog/Optimizely/etc
        """

        if traffic_split is None:
            # Equal split
            split_percent = 100 / len(variants)
            traffic_split = {v['id']: split_percent for v in variants}

        return {
            'experiment_name': f'ab_test_{datetime.now().strftime("%Y%m%d_%H%M")}',
            'variants': [
                {
                    'id': v['id'],
                    'name': v['name'],
                    'traffic_percentage': traffic_split.get(v['id'], 0)
                }
                for v in variants
            ],
            'metrics': variants[0]['metrics_to_track'] if variants else [],
            'duration_days': 14,
            'minimum_sample_size': 1000,
            'significance_level': 0.05,
            'implementation': {
                'type': 'git_branches',
                'branches': [v.get('branch_name', 'main') for v in variants]
            }
        }


# Test function
def test_ab_generator():
    """Test A/B test generator"""

    # Create a test project path
    import tempfile
    temp_dir = tempfile.mkdtemp()

    generator = ABTestGenerator(temp_dir)

    # Generate variants
    variants = generator.generate_variants(variant_count=3)

    print("Generated Variants:")
    for variant in variants:
        print(f"\n{variant['name']}:")
        print(f"  ID: {variant['id']}")
        print(f"  Branch: {variant['branch_name']}")
        print(f"  Description: {variant['description']}")
        print(f"  File modifications: {len(variant['file_modifications'])}")

    # Generate experiment config
    config = generator.generate_experiment_config(variants)
    print("\n\nExperiment Config:")
    print(json.dumps(config, indent=2))


if __name__ == "__main__":
    test_ab_generator()
