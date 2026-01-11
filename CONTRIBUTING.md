# Contributing to Multi-Agent Team

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
source venv/bin/activate  # On Windows: venv\Scripts\activate

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
