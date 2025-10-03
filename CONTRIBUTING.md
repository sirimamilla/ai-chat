# Contributing to AI Chat

Thank you for your interest in contributing to AI Chat! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/ai-chat.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Set up the development environment

## Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest black pylint mypy

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python main.py init-database
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write docstrings for all public functions and classes
- Keep functions focused and modular

### Formatting

We use `black` for code formatting:

```bash
black src/
```

### Linting

We use `pylint` for linting:

```bash
pylint src/ai_chat
```

### Type Checking

We use `mypy` for type checking:

```bash
mypy src/ai_chat
```

## Testing

Write tests for new features and bug fixes:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/ai_chat

# Run specific test file
pytest tests/test_agent.py
```

## Commit Guidelines

- Use clear, descriptive commit messages
- Start with a verb in present tense (e.g., "Add", "Fix", "Update")
- Reference issue numbers when applicable

Example:
```
Add dynamic tool selection feature

- Implement ToolSelector class
- Add keyword-based tool matching
- Update documentation

Fixes #123
```

## Pull Request Process

1. Update documentation for any changed functionality
2. Add tests for new features
3. Ensure all tests pass
4. Update CHANGELOG.md if applicable
5. Submit pull request with clear description

### Pull Request Checklist

- [ ] Code follows project style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] No merge conflicts

## Areas for Contribution

- **Features**: New MCP integrations, tool capabilities
- **Documentation**: Improvements, examples, tutorials
- **Testing**: Additional test coverage
- **Bug Fixes**: Issue resolution
- **Performance**: Optimization improvements

## Questions?

Feel free to:
- Open an issue for bugs or feature requests
- Start a discussion for general questions
- Contact maintainers for guidance

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help create a welcoming environment

Thank you for contributing!
