"""
Generate Essentials Script

One-command generation of all essential features identified by agents:
- CLI Interface
- Docker deployment
- Workflow templates (10+)
- REST API
- Community files

Usage:
    python generate_essentials.py --all
    python generate_essentials.py --cli
    python generate_essentials.py --docker
    python generate_essentials.py --templates
"""

import click
import json
from pathlib import Path
from datetime import datetime
from code_generators import CodeGenerator, generate_all_quick_wins
from action_synthesizer import ActionSynthesizer, generate_project_plan_from_outputs


@click.command()
@click.option('--all', 'gen_all', is_flag=True, help='Generate all essentials')
@click.option('--cli', is_flag=True, help='Generate CLI interface')
@click.option('--docker', is_flag=True, help='Generate Docker files')
@click.option('--templates', is_flag=True, help='Generate workflow templates')
@click.option('--api', is_flag=True, help='Generate REST API')
@click.option('--community', is_flag=True, help='Generate community files')
@click.option('--project-plan', is_flag=True, help='Generate PROJECT_PLAN.md from latest export')
@click.option('--export-file', type=click.Path(exists=True), help='Path to agent output export file')
def main(gen_all, cli, docker, templates, api, community, project_plan, export_file):
    """Generate essential features for Multi-Agent Platform"""

    click.echo("[RUN] Multi-Agent Team - Essentials Generator\n")

    generator = CodeGenerator()

    # If no specific options, show help
    if not any([gen_all, cli, docker, templates, api, community, project_plan]):
        click.echo("Usage: python generate_essentials.py [OPTIONS]\n")
        click.echo("Options:")
        click.echo("  --all            Generate all essentials")
        click.echo("  --cli            Generate CLI interface")
        click.echo("  --docker         Generate Docker files")
        click.echo("  --templates      Generate workflow templates")
        click.echo("  --api            Generate REST API")
        click.echo("  --community      Generate community files")
        click.echo("  --project-plan   Generate PROJECT_PLAN.md")
        click.echo("  --export-file    Specify export file for project plan")
        return

    # Generate PROJECT_PLAN.md
    if project_plan:
        click.echo("[PLAN] Generating PROJECT_PLAN.md...\n")

        # Find latest export if not specified
        if not export_file:
            exports_dir = Path("exports")
            if exports_dir.exists():
                json_exports = list(exports_dir.glob("*.json"))
                if json_exports:
                    export_file = max(json_exports, key=lambda p: p.stat().st_mtime)
                    click.echo(f"Using latest export: {export_file}")

        if not export_file:
            click.echo("[X] No export file found. Run the platform first or specify --export-file")
            return

        # Load export
        with open(export_file, 'r') as f:
            data = json.load(f)

        # Generate project plan
        project_name = data['metadata'].get('project_name', 'Multi-Agent Project')
        agent_outputs = data['agent_outputs']

        plan = generate_project_plan_from_outputs(agent_outputs, project_name)

        # Write plan with UTF-8 encoding
        with open('PROJECT_PLAN.md', 'w', encoding='utf-8') as f:
            f.write(plan)

        click.echo("[OK] Created: PROJECT_PLAN.md")
        click.echo("\n[FILE] Review your project plan and start building!\n")

    # Generate All
    if gen_all:
        click.echo("[GEN] Generating all essentials...\n")

        results = generate_all_quick_wins()

        # Show results
        for feature, files in results.items():
            click.echo(f"\n[OK] {feature.upper()}")
            for file in files:
                click.echo(f"   +-- {file}")

        click.echo("\n[SUCCESS] All essentials generated!\n")
        click.echo("Next steps:")
        click.echo("  1. Review generated files")
        click.echo("  2. Install CLI: pip install -e .")
        click.echo("  3. Run: multi-agent --help")
        click.echo("  4. Docker: docker-compose up")
        return

    # Generate individual features
    if cli:
        click.echo("[CLI] Generating CLI interface...\n")
        files = generator.generate_cli_starter()
        created = generator.write_files(files)
        for file in created:
            click.echo(f"[OK] Created: {file}")
        click.echo("\nInstall with: pip install -e .")
        click.echo("Run with: multi-agent --help\n")

    if docker:
        click.echo("[DOCKER] Generating Docker files...\n")
        files = generator.generate_docker_files()
        created = generator.write_files(files)
        for file in created:
            click.echo(f"[OK] Created: {file}")
        click.echo("\nRun with: docker-compose up\n")

    if templates:
        click.echo("[TEMPLATES] Generating workflow templates...\n")
        files = generator.generate_workflow_templates()
        templates_dir = Path("templates")
        created = generator.write_files(files, str(templates_dir))
        click.echo(f"[OK] Created {len(created)} templates:")
        for file in created:
            click.echo(f"   +-- {file}")
        click.echo("")

    if api:
        click.echo("[API] Generating REST API...\n")
        files = generator.generate_api_starter()
        created = generator.write_files(files)
        for file in created:
            click.echo(f"[OK] Created: {file}")
        click.echo("\nRun with: python api_server.py\n")

    if community:
        click.echo("[COMMUNITY] Generating community files...\n")
        files = generator.generate_community_files()
        created = generator.write_files(files)
        for file in created:
            click.echo(f"[OK] Created: {file}")
        click.echo("")

    click.echo("[DONE] Check the generated files and customize as needed.\n")


if __name__ == "__main__":
    main()
