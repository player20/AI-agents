"""
Code Generators - Automatically generate starter code for common features

This module provides code generation for:
- CLI Interface
- Docker deployment files
- Workflow templates
- REST API
- Community files (CONTRIBUTING.md, CODE_OF_CONDUCT.md)
"""

import os
from pathlib import Path
from typing import Dict, List


class CodeGenerator:
    """Generates starter code for various features"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()

    def generate_cli_starter(self) -> Dict[str, str]:
        """Generate CLI interface using Click"""

        cli_code = '''"""
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

    click.echo("📚 Available Templates:\\n")

    for template in templates:
        # Load template to show description
        with open(template, 'r') as f:
            config = yaml.safe_load(f)

        name = template.stem.replace('-', ' ').title()
        description = config.get('description', 'No description')[:80]
        agents_count = len(config.get('agents', []))

        click.echo(f"  • {name}")
        click.echo(f"    {description}")
        click.echo(f"    Agents: {agents_count}\\n")


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
    click.echo(f"\\nRun with: multi-agent run {filepath}")


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
    click.echo(f"💰 Model: {metadata.get('model_preset')}\\n")

    # Show agent outputs
    for agent, output in agent_outputs.items():
        click.echo(f"\\n{'='*60}")
        click.echo(f"🤖 {agent} Agent")
        click.echo(f"{'='*60}\\n")

        # Show first 500 chars
        output_text = output.get('full_output', '')
        if len(output_text) > 500:
            click.echo(output_text[:500] + "...\\n(truncated)")
        else:
            click.echo(output_text)


@cli.command()
def init():
    """Initialize a new multi-agent project"""

    click.echo("🚀 Initializing Multi-Agent Team project...\\n")

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
    click.echo("\\n🎉 Project initialized! Run 'multi-agent list-templates' to get started.")


if __name__ == "__main__":
    cli()
'''

        return {
            "multi_agent_cli.py": cli_code,
            "setup.py": self._generate_setup_py(),
            "requirements_cli.txt": "click>=8.0.0\\npyyaml>=6.0\\n"
        }

    def generate_docker_files(self) -> Dict[str, str]:
        """Generate Docker deployment files"""

        dockerfile = '''# Multi-Agent Team Platform - Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p templates exports projects

# Expose Gradio port
EXPOSE 7860

# Set environment variables
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT=7860

# Run the application
CMD ["python", "multi_agent_team.py"]
'''

        docker_compose = '''version: '3.8'

services:
  multi-agent-team:
    build: .
    container_name: multi-agent-platform
    ports:
      - "7860:7860"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GRADIO_SERVER_NAME=0.0.0.0
    volumes:
      - ./exports:/app/exports
      - ./projects:/app/projects
      - ./templates:/app/templates
      - ./team_memory.json:/app/team_memory.json
    restart: unless-stopped

  # Optional: PostgreSQL for future enterprise features
  # postgres:
  #   image: postgres:15-alpine
  #   container_name: multi-agent-db
  #   environment:
  #     - POSTGRES_DB=multiagent
  #     - POSTGRES_USER=admin
  #     - POSTGRES_PASSWORD=${DB_PASSWORD}
  #   volumes:
  #     - postgres_data:/var/lib/postgresql/data
  #   ports:
  #     - "5432:5432"

# volumes:
#   postgres_data:
'''

        dockerignore = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project
exports/
projects/
*.log
.env
.env.local

# Git
.git/
.gitignore
'''

        docker_readme = '''# Docker Deployment

## Quick Start

1. **Set your API key**:
   ```bash
   echo "ANTHROPIC_API_KEY=your_key_here" > .env
   ```

2. **Build and run**:
   ```bash
   docker-compose up -d
   ```

3. **Access the platform**:
   Open http://localhost:7860

## Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# Access container shell
docker-compose exec multi-agent-team bash
```

## Production Deployment

For production, consider:

1. **Use secrets management** instead of .env file
2. **Enable SSL/TLS** with reverse proxy (nginx, Caddy)
3. **Set up monitoring** (Prometheus, Grafana)
4. **Enable database** (uncomment PostgreSQL in docker-compose.yml)
5. **Scale with** Kubernetes or Docker Swarm

## Environment Variables

- `ANTHROPIC_API_KEY` - Required: Your Anthropic API key
- `GRADIO_SERVER_NAME` - Default: 0.0.0.0
- `GRADIO_SERVER_PORT` - Default: 7860
- `DB_PASSWORD` - Optional: PostgreSQL password (if using database)
'''

        return {
            "Dockerfile": dockerfile,
            "docker-compose.yml": docker_compose,
            ".dockerignore": dockerignore,
            "DOCKER_README.md": docker_readme
        }

    def generate_workflow_templates(self) -> Dict[str, str]:
        """Generate 10+ workflow templates"""

        templates = {}

        # 1. SaaS App Planner
        templates["saas-app-planner.yaml"] = '''name: SaaS App Planner
description: Plan a complete SaaS application with market research, features, and architecture
agents:
  - Memory
  - Research
  - Ideas
  - Designs
  - Senior
  - QA
model: balanced
code_review_mode: false
'''

        # 2. Code Review
        templates["code-review.yaml"] = '''name: Code Review Automation
description: Comprehensive code review with architecture, security, and testing analysis
agents:
  - Senior
  - QA
  - Verifier
model: quality
code_review_mode: true
'''

        # 3. Market Research
        templates["market-research.yaml"] = '''name: Market Research & Validation
description: Analyze market opportunity, competitors, and strategic positioning
agents:
  - Memory
  - Research
  - Ideas
  - Senior
model: balanced
code_review_mode: false
'''

        # 4. Security Audit
        templates["security-audit.yaml"] = '''name: Security Audit
description: Comprehensive security and compliance review
agents:
  - Senior
  - Verifier
model: quality
code_review_mode: true
'''

        # 5. API Design
        templates["api-design.yaml"] = '''name: API Design
description: Design RESTful or GraphQL APIs with best practices
agents:
  - Research
  - Ideas
  - Senior
  - Designs
  - QA
model: balanced
code_review_mode: false
'''

        # 6. Database Schema Design
        templates["database-schema.yaml"] = '''name: Database Schema Design
description: Design scalable database schemas with optimization recommendations
agents:
  - Research
  - Senior
  - QA
model: balanced
code_review_mode: false
'''

        # 7. Feature Specification
        templates["feature-spec.yaml"] = '''name: Feature Specification
description: Create detailed feature specifications with acceptance criteria
agents:
  - Research
  - Ideas
  - Designs
  - QA
model: balanced
code_review_mode: false
'''

        # 8. Bug Analysis
        templates["bug-analysis.yaml"] = '''name: Bug Analysis & Root Cause
description: Analyze bugs, identify root causes, and recommend fixes
agents:
  - Senior
  - QA
  - Verifier
model: quality
code_review_mode: true
'''

        # 9. Performance Optimization
        templates["performance-optimization.yaml"] = '''name: Performance Optimization
description: Identify performance bottlenecks and optimization strategies
agents:
  - Senior
  - QA
model: balanced
code_review_mode: true
'''

        # 10. Technical Documentation
        templates["technical-docs.yaml"] = '''name: Technical Documentation
description: Generate comprehensive technical documentation
agents:
  - Research
  - Senior
  - Designs
model: balanced
code_review_mode: false
'''

        # 11. Mobile App Planning
        templates["mobile-app-planning.yaml"] = '''name: Mobile App Planning
description: Plan iOS and Android mobile applications
agents:
  - Research
  - Ideas
  - Designs
  - iOS
  - Android
  - QA
model: balanced
code_review_mode: false
'''

        # 12. Full Stack Development
        templates["full-stack-dev.yaml"] = '''name: Full Stack Development
description: Complete development lifecycle from planning to deployment
agents:
  - PM
  - Memory
  - Research
  - Ideas
  - Designs
  - iOS
  - Android
  - Web
  - Senior
  - QA
  - Verifier
model: balanced
code_review_mode: false
'''

        return templates

    def generate_api_starter(self) -> Dict[str, str]:
        """Generate REST API starter with FastAPI"""

        api_code = '''"""
Multi-Agent Team REST API

FastAPI-based REST API for running agent workflows programmatically.

Endpoints:
    POST /api/workflows - Run a workflow
    GET /api/workflows/{id} - Get workflow status
    GET /api/templates - List available templates
    POST /api/export - Export results
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import json

app = FastAPI(
    title="Multi-Agent Team API",
    description="REST API for AI agent orchestration",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (replace with database for production)
workflows_db = {}


class WorkflowRequest(BaseModel):
    agents: List[str]
    description: str
    model: str = "balanced"
    code_review_mode: bool = False


class WorkflowResponse(BaseModel):
    workflow_id: str
    status: str
    created_at: str


class WorkflowStatus(BaseModel):
    workflow_id: str
    status: str
    progress: int
    results: Optional[Dict[str, Any]] = None


@app.get("/")
def read_root():
    return {
        "name": "Multi-Agent Team API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.post("/api/workflows", response_model=WorkflowResponse)
async def create_workflow(
    request: WorkflowRequest,
    background_tasks: BackgroundTasks
):
    """
    Create and run a new workflow

    Returns immediately with workflow_id for tracking
    """

    workflow_id = str(uuid.uuid4())

    # Store workflow
    workflows_db[workflow_id] = {
        "id": workflow_id,
        "status": "pending",
        "request": request.dict(),
        "created_at": datetime.now().isoformat(),
        "progress": 0,
        "results": None
    }

    # Run workflow in background
    background_tasks.add_task(run_workflow_task, workflow_id, request)

    return WorkflowResponse(
        workflow_id=workflow_id,
        status="pending",
        created_at=workflows_db[workflow_id]["created_at"]
    )


@app.get("/api/workflows/{workflow_id}", response_model=WorkflowStatus)
def get_workflow_status(workflow_id: str):
    """Get the status of a workflow"""

    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow = workflows_db[workflow_id]

    return WorkflowStatus(
        workflow_id=workflow["id"],
        status=workflow["status"],
        progress=workflow["progress"],
        results=workflow.get("results")
    )


@app.get("/api/templates")
def list_templates():
    """List all available workflow templates"""

    # TODO: Read from templates directory
    return {
        "templates": [
            {
                "name": "SaaS App Planner",
                "file": "saas-app-planner.yaml",
                "agents": ["Memory", "Research", "Ideas", "Designs", "Senior", "QA"]
            },
            {
                "name": "Code Review",
                "file": "code-review.yaml",
                "agents": ["Senior", "QA", "Verifier"]
            },
            # Add more templates
        ]
    }


@app.post("/api/export/{workflow_id}")
def export_workflow(workflow_id: str, format: str = "json"):
    """Export workflow results in specified format"""

    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow = workflows_db[workflow_id]

    if workflow["status"] != "completed":
        raise HTTPException(status_code=400, detail="Workflow not completed")

    results = workflow["results"]

    if format == "json":
        return results
    elif format == "markdown":
        # TODO: Convert to markdown
        return {"error": "Markdown export not implemented"}
    else:
        raise HTTPException(status_code=400, detail="Invalid format")


def run_workflow_task(workflow_id: str, request: WorkflowRequest):
    """Background task to run the workflow"""

    try:
        workflows_db[workflow_id]["status"] = "running"
        workflows_db[workflow_id]["progress"] = 10

        # TODO: Integrate with actual multi-agent system
        # For now, simulate workflow execution

        workflows_db[workflow_id]["progress"] = 50

        # Simulate results
        results = {
            "metadata": {
                "workflow_id": workflow_id,
                "agents": request.agents,
                "model": request.model
            },
            "agent_outputs": {
                agent: f"Output from {agent} agent"
                for agent in request.agents
            }
        }

        workflows_db[workflow_id]["status"] = "completed"
        workflows_db[workflow_id]["progress"] = 100
        workflows_db[workflow_id]["results"] = results

    except Exception as e:
        workflows_db[workflow_id]["status"] = "failed"
        workflows_db[workflow_id]["error"] = str(e)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''

        return {
            "api_server.py": api_code,
            "requirements_api.txt": "fastapi>=0.109.0\\nuvicorn[standard]>=0.27.0\\npydantic>=2.0.0\\n"
        }

    def generate_community_files(self) -> Dict[str, str]:
        """Generate open-source community files"""

        contributing = '''# Contributing to Multi-Agent Team

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository**
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/multi-agent-team.git
   cd multi-agent-team
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Create a branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Setting Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up pre-commit hooks (optional)
pre-commit install
```

### Making Changes

1. **Make your changes** in your feature branch
2. **Write tests** for new functionality
3. **Run tests**:
   ```bash
   pytest tests/
   ```
4. **Check code style**:
   ```bash
   black .
   flake8 .
   ```

### Committing Changes

- Write clear, descriptive commit messages
- Follow [Conventional Commits](https://www.conventionalcommits.org/)
  - `feat:` for new features
  - `fix:` for bug fixes
  - `docs:` for documentation
  - `test:` for tests
  - `refactor:` for refactoring

Example:
```
feat: add CLI interface for running workflows

- Implement Click-based CLI
- Add commands for run, list-templates, create-template
- Include tests for all commands
```

### Submitting Pull Requests

1. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request** on GitHub:
   - Provide clear title and description
   - Reference any related issues
   - Include screenshots/examples if applicable

3. **Respond to feedback**:
   - Address reviewer comments
   - Update your branch as needed

## Types of Contributions

### Bug Reports

When reporting bugs, include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment (OS, Python version, etc.)
- Error messages/stack traces

### Feature Requests

When suggesting features:
- Describe the problem it solves
- Provide use cases
- Consider implementation complexity
- Discuss alternatives

### Code Contributions

Priority areas:
- **Quick Wins**: CLI, Docker, Templates
- **Community Features**: Documentation, examples, tutorials
- **Enterprise Features**: SSO, audit logging, RBAC
- **No-Code Features**: Visual workflow builder
- **Developer Experience**: API, SDK, VS Code extension

### Documentation

- Fix typos and errors
- Improve clarity and examples
- Add tutorials and guides
- Translate to other languages

## Code Style

- Follow PEP 8
- Use Black for formatting
- Use type hints where possible
- Write docstrings for public functions
- Keep functions focused and small

## Testing

- Write unit tests for new features
- Maintain test coverage above 80%
- Test edge cases and error conditions
- Use pytest for testing

## Community

- Be respectful and inclusive
- Follow our [Code of Conduct](CODE_OF_CONDUCT.md)
- Ask questions in Discussions
- Help others in Issues

## License

By contributing, you agree that your contributions will be licensed under the MIT License (or project license).

---

Thank you for contributing to Multi-Agent Team! 🎉
'''

        code_of_conduct = '''# Code of Conduct

## Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

## Our Standards

**Positive behavior includes:**

- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards others

**Unacceptable behavior includes:**

- Harassment, trolling, or discriminatory comments
- Publishing others' private information
- Inappropriate sexual attention or advances
- Other conduct inappropriate in a professional setting

## Enforcement

Project maintainers are responsible for clarifying standards and will take appropriate action in response to unacceptable behavior.

Report incidents to: [PROJECT_EMAIL]

## Attribution

Adapted from the [Contributor Covenant](https://www.contributor-covenant.org/), version 2.1.
'''

        readme_template = '''# Multi-Agent Team Platform

> Open-Source AI Agent Orchestration with Enterprise Features

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## ✨ Features

- 🤖 **11 Specialized AI Agents** - PM, Research, Ideas, Designs, iOS/Android/Web, QA, Verifier
- 🎯 **Agent Selection & Presets** - Run specific agents for different workflows
- 🔄 **Multi-Model Support** - Intelligent fallback (Opus → Sonnet → Haiku)
- 📊 **Action Board** - Transforms analysis into executable next steps
- 🚀 **Code Generation** - Auto-generate CLI, Docker, templates from analysis
- 📤 **Export Formats** - JSON, Markdown, CSV
- 🛡️ **Anti-Hallucination** - Built-in epistemic accuracy system
- 🔧 **Git Integration** - Auto-apply suggestions to codebases

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Set API Key

```bash
export ANTHROPIC_API_KEY=your_key_here
```

### Run the Platform

```bash
python multi_agent_team.py
```

Visit http://localhost:7860

## 📖 Documentation

- [Quick Start Guide](QUICK_START.md)
- [Feature Documentation](README_ENHANCED.md)
- [CLI Reference](CLI_GUIDE.md)
- [Docker Deployment](DOCKER_README.md)
- [API Documentation](API_DOCS.md)

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=YOUR_USERNAME/multi-agent-team&type=Date)](https://star-history.com/#YOUR_USERNAME/multi-agent-team&Date)
'''

        return {
            "CONTRIBUTING.md": contributing,
            "CODE_OF_CONDUCT.md": code_of_conduct,
            "README.md": readme_template
        }

    def _generate_setup_py(self) -> str:
        """Generate setup.py for CLI package"""
        return '''from setuptools import setup, find_packages

setup(
    name="multi-agent-cli",
    version="1.0.0",
    description="CLI for Multi-Agent Team Platform",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "pyyaml>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "multi-agent=multi_agent_cli:cli",
        ],
    },
    python_requires=">=3.8",
)
'''

    def write_files(self, files: Dict[str, str], output_dir: str = None) -> List[str]:
        """
        Write generated files to disk

        Args:
            files: Dict of filename -> content
            output_dir: Optional output directory (defaults to project root)

        Returns:
            List of created file paths
        """
        created_files = []
        base_dir = Path(output_dir or self.project_root)

        for filename, content in files.items():
            filepath = base_dir / filename

            # Create parent directories
            filepath.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            created_files.append(str(filepath))

        return created_files


# Convenience functions

def generate_all_quick_wins(output_dir: str = None) -> Dict[str, List[str]]:
    """
    Generate all quick win features

    Returns dict of feature_name -> list of created files
    """
    generator = CodeGenerator()

    results = {
        "cli": [],
        "docker": [],
        "templates": [],
        "api": [],
        "community": []
    }

    # Generate CLI
    cli_files = generator.generate_cli_starter()
    results["cli"] = generator.write_files(cli_files, output_dir)

    # Generate Docker
    docker_files = generator.generate_docker_files()
    results["docker"] = generator.write_files(docker_files, output_dir)

    # Generate Templates
    template_files = generator.generate_workflow_templates()
    templates_dir = Path(output_dir or generator.project_root) / "templates"
    results["templates"] = generator.write_files(template_files, str(templates_dir))

    # Generate API
    api_files = generator.generate_api_starter()
    results["api"] = generator.write_files(api_files, output_dir)

    # Generate Community Files
    community_files = generator.generate_community_files()
    results["community"] = generator.write_files(community_files, output_dir)

    return results
