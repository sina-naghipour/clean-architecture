### 1. Fork and Clone
```bash
git clone https://github.com/your-username/clean-arch.git
cd clean-arch/kata-refactors
```

### 2. Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .  # Install package in development mode

# Setup pre-commit hooks
pre-commit install
```

### 3. Create Feature Branch
```bash
git checkout -b feature/description
# Examples:
# git checkout -b feature/tennis-game-refactor
# git checkout -b fix/scoring-logic
```

### 4. Make Changes
- Follow Clean Code principles
- Write tests for new functionality
- Use type hints and docstrings
- Keep functions small and focused

### 5. Testing & Quality Checks
```bash
# Run tests with coverage
pytest --cov=src --cov-report=term-missing

# Run all code quality checks
pre-commit run --all-files

# Individual checks (if needed)
ruff check .    # Linting
mypy src        # Type checking
ruff format .   # Formatting
```

### 6. Commit Changes
```bash
git add .
git commit -m "feat: descriptive commit message"
# Conventional commit types:
# feat: new feature
# fix: bug fix
# docs: documentation
# refactor: code restructuring
# test: adding tests
```

### 7. Push and Create PR
```bash
git push origin feature/description
```
Then create a Pull Request on GitHub with:
- Descriptive title: "Stage N – Description"
- Production-readiness checklist
- Links to CI run, coverage reports
- EVIDENCE.md with code snippets

## Code Standards

### Clean Code Principles
- **Meaningful Names**: `player1_score` not `p1`
- **Small Functions**: < 20 lines, single responsibility
- **Type Hints**: All function signatures

### Testing Requirements
- ≥80% test coverage
- Test both happy paths and edge cases
- One intentional failing test scenario (TDD flow)
- Clear test names:
`test_idiom_to_score_translation`

### Architecture Rules
- Business logic in `src/` domain
- Tests in `tests/` mirroring source structure
- No business logic in tests
- Dependency injection for testability

## Pull Request Process

### PR Checklist
- [ ] All tests pass (≥80% coverage)
- [ ] Pre-commit hooks pass
- [ ] Type checking passes
- [ ] Code follows Clean Architecture
- [ ] Documentation updated
- [ ] EVIDENCE.md included

### PR Title Format
```
Stage <N> – <Description>
Examples:
Stage 1 – Stage 1 – Clean Architecture Tennis Game
```

### PR Description Template
```markdown
## Stage N – Description

### Links:
- Repository: [link]
- CI Run: [link]
- Coverage Report: [link]
- ADRs: [link]

### Changes:
- [Summary of changes]

### Evidence:
See EVIDENCE.md for implementation details.
```

## Getting Help

- Check RUNBOOK.md for operational procedures
- Review ADR-001.md for architecture decisions
- Examine existing tests for patterns
- Run `pytest -v` to see test execution details

## Quick Start for New Contributors

```bash
# One-time setup
git clone <repo>
cd kata-refactors
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
pre-commit install

# Verify setup works
pytest --cov=src
python -c "from tennis.game import TennisGame; print('✓ Setup complete')"
```

## Running Each API Service

during development you could head over to app folder of any service and run this command in order to run each service separate.

```bash
python main.py
```

## Testing Each Service

run `pytest` inside the app directory of any service.

```bash 
(.auth-venv) PS D:\codes\remote\New Stages\clean-architecture\api\auth\app> pytest -v
```

## Virtual Environment

create a virtual enviroment for any service you desire to develop to have isolated environments.

```bash
python -m venv .venv-ServiceName
```

## Python Magic Issue

to run `products` service in windows, you need to change the requirements in `products` service.

```text
# change this to
python-magic

# this
python-magic-bin
```

## Docusaurus Regeneration

docusaurus has compatibility issues between `docusaurus-plugin-openapi-docs` and `docusaurus-theme-openapi-docs` if ever ran into any kind of problems, you could generate docusuarus all over again using commands below:

### 1. Downgrade Docusaurus to 3.8.1:

**Remove current versions**
```bash
yarn remove @docusaurus/core @docusaurus/preset-classic
```
**Install compatible versions**
```bash
yarn add @docusaurus/core@3.8.1 @docusaurus/preset-classic@3.8.1 @docusaurus/module-type-aliases@3.8.1
```
**Also update/create-react-app if you have it**
```bash
yarn add react@^18 react-dom@^18
```
### 2. Update your package.json dependencies:
Make sure it looks like this:

```json
{
  "dependencies": {
    "@docusaurus/core": "3.8.1",
    "@docusaurus/preset-classic": "3.8.1",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "docusaurus-plugin-openapi-docs": "4.5.1",
    "docusaurus-theme-openapi-docs": "4.5.1"
  },
  "devDependencies": {
    "@docusaurus/module-type-aliases": "3.8.1"
  }
}
```
### 3. Clear everything and reinstall:

**Remove node_modules and lock files**
```bash
rm -rf node_modules
rm -f yarn.lock package-lock.json
```

**Clear Docusaurus cache**
```bash
rm -rf .docusaurus
```
**Reinstall**
```bash
yarn install
```

**Regenerate API docs**
```bash
yarn docusaurus gen-api-docs api
```

**Start**
```bash
yarn start
```
### 4. Alternative: Check for newer OpenAPI plugin version:
Sometimes there might be a newer version that supports Docusaurus 3.9.2: