# Contributing Guide

## Development Workflow
1. Fork and clone the repository
2. Create virtual environment: `python -m venv venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Install pre-commit: `pre-commit install`
5. Create feature branch: `git checkout -b feature/description`
6. Make changes and test: `pytest --cov`
7. Run pre-commit: `pre-commit run --all-files`
8. Push and create PR

## Code Standards
- Follow Clean Code principles (meaningful names, small functions)
- Write tests for new functionality
- Maintain ≥80% test coverage
- Use type hints and docstrings
