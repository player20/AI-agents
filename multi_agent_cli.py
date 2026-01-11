"""
Multi-Agent Team CLI

Command-line interface for running agent workflows, creating templates, and more.

Usage:
    multi-agent run workflow.yaml
    multi-agent list-templates
    multi-agent create-template --name "My Workflow"
    multi-agent export --format json
"""

import click
import yaml
import json
from pathlib import Path
from multi_agent_team import run_workflow, list_agent_presets, export_results


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Multi-Agent Team CLI - AI agent orchestration from the command line"""
    pass


@cli.command()
@click.argument("workflow_file", type=click.Path(exists=True))
@click.option("--model", "-m", default="balanced", help="Model preset: speed, balanced, quality, premium")
@click.option("--export", "-e", is_flag=True, help="Auto-export results")
@click.option("--output", "-o", type=click.Path(), help="Output directory for exports")
def run(workflow_file, model, export, output):
    """Run an agent workflow from a YAML file"""

    click.echo(f"🚀 Running workflow: {workflow_file}")

    # Load workflow configuration
    with open(workflow_file, 'r') as f:
        config = yaml.safe_load(f)

    # Extract configuration
    agents = config.get('agents', [])
    project_description = config.get('description', '')
    model_preset = config.get('model', model)

    click.echo(f"📋 Agents: {', '.join(agents)}")
    click.echo(f"🤖 Model: {model_preset}")

    # Run the workflow
    results = run_workflow(
        agents=agents,
        description=project_description,
        model_preset=model_preset
    )

    click.echo("✅ Workflow completed successfully!")

    # Export if requested
    if export:
        export_dir = output or "./exports"
        Path(export_dir).mkdir(parents=True, exist_ok=True)

        timestamp = results['metadata']['timestamp']
        project_name = results['metadata'].get('project_name', 'workflow')

        # Export to JSON
        json_path = f"{export_dir}/{project_name}_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2)

        click.echo(f"📄 Exported to: {json_path}")


@cli.command()
def list_templates():
    """List available workflow templates"""

    templates_dir = Path("templates")

    if not templates_dir.exists():
        click.echo("❌ No templates directory found")
        return

    templates = list(templates_dir.glob("*.yaml"))

    if not templates:
        click.echo("📭 No templates found")
        return

    click.echo("📚 Available Templates:\n")

    for template in templates:
        # Load template to show description
        with open(template, 'r') as f:
            config = yaml.safe_load(f)

        name = template.stem.replace('-', ' ').title()
        description = config.get('description', 'No description')[:80]
        agents_count = len(config.get('agents', []))

        click.echo(f"  • {name}")
        click.echo(f"    {description}")
        click.echo(f"    Agents: {agents_count}\n")


@cli.command()
@click.option("--name", "-n", prompt="Template name", help="Name for the workflow template")
@click.option("--agents", "-a", prompt="Agents (comma-separated)", help="Agents to include")
@click.option("--description", "-d", prompt="Description", help="Workflow description")
def create_template(name, agents, description):
    """Create a new workflow template"""

    # Parse agents
    agent_list = [a.strip() for a in agents.split(',')]

    # Create template structure
    template = {
        'name': name,
        'description': description,
        'agents': agent_list,
        'model': 'balanced',
        'code_review_mode': False
    }

    # Save template
    templates_dir = Path("templates")
    templates_dir.mkdir(exist_ok=True)

    filename = name.lower().replace(' ', '-') + '.yaml'
    filepath = templates_dir / filename

    with open(filepath, 'w') as f:
        yaml.dump(template, f, default_flow_style=False)

    click.echo(f"✅ Template created: {filepath}")
    click.echo(f"\nRun with: multi-agent run {filepath}")


@cli.command()
@click.argument("export_file", type=click.Path(exists=True))
@click.option("--format", "-f", type=click.Choice(['json', 'markdown', 'csv']), default='json')
def view(export_file, format):
    """View an exported workflow result"""

    with open(export_file, 'r') as f:
        data = json.load(f)

    metadata = data.get('metadata', {})
    agent_outputs = data.get('agent_outputs', {})

    click.echo(f"📊 Project: {metadata.get('project_name')}")
    click.echo(f"📅 Date: {metadata.get('timestamp')}")
    click.echo(f"🤖 Agents: {', '.join(metadata.get('selected_agents', []))}")
    click.echo(f"💰 Model: {metadata.get('model_preset')}\n")

    # Show agent outputs
    for agent, output in agent_outputs.items():
        click.echo(f"\n{'='*60}")
        click.echo(f"🤖 {agent} Agent")
        click.echo(f"{'='*60}\n")

        # Show first 500 chars
        output_text = output.get('full_output', '')
        if len(output_text) > 500:
            click.echo(output_text[:500] + "...\n(truncated)")
        else:
            click.echo(output_text)


@cli.command()
def init():
    """Initialize a new multi-agent project"""

    click.echo("🚀 Initializing Multi-Agent Team project...\n")

    # Create directory structure
    dirs = ['templates', 'exports', 'projects']
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        click.echo(f"✅ Created: {dir_name}/")

    # Create default config
    config = {
        'version': '1.0',
        'default_model': 'balanced',
        'export_format': ['json', 'markdown']
    }

    with open('config.yaml', 'w') as f:
        yaml.dump(config, f)

    click.echo("✅ Created: config.yaml")
    click.echo("\n🎉 Project initialized! Run 'multi-agent list-templates' to get started.")


if __name__ == "__main__":
    cli()
