# Contributing to ROMA-01

First off, thank you for considering contributing to ROMA-01! It's people like you that make ROMA-01 such a great tool.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)
- [Community](#community)

---

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to lukema95@github.com.

---

## How Can I Contribute?

### 🐛 Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates.

**How to Submit a Good Bug Report:**

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples** (code snippets, config files)
- **Describe the behavior you observed** and what you expected
- **Include logs** if applicable
- **Specify your environment:**
  - OS: [e.g., macOS 14.0, Ubuntu 22.04]
  - Python version: [e.g., 3.12.0]
  - Node.js version: [e.g., 18.17.0]
  - AI-01 version: [e.g., 1.1.0]

**Template:**
```markdown
**Bug Description:**
A clear description of what the bug is.

**To Reproduce:**
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior:**
What you expected to happen.

**Screenshots/Logs:**
If applicable, add screenshots or log output.

**Environment:**
- OS: 
- Python: 
- Node.js: 
- ROMA-01 version: 
```

### 💡 Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues.

**Before Submitting:**
- Check if the enhancement has already been suggested
- Determine if it fits the project's scope
- Be as detailed as possible

**Template:**
```markdown
**Enhancement Description:**
Clear description of the suggested enhancement.

**Motivation:**
Why would this be useful?

**Possible Implementation:**
Any ideas on how to implement this?

**Alternatives:**
Any alternative solutions or features considered?
```

### 🔧 Contributing Code

#### Types of Contributions We're Looking For:

- 🐛 Bug fixes
- ✨ New features (discuss in issues first)
- 📝 Documentation improvements
- 🧪 Test coverage improvements
- 🎨 UI/UX enhancements
- ⚡ Performance improvements
- 🌐 Internationalization (i18n)
- 🔌 New exchange integrations
- 🤖 New LLM provider integrations

---

## Development Setup

### Prerequisites

- Python 3.12 or 3.13 (NOT 3.14)
- Node.js 18+
- Git

### Fork & Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/lukema95/roma-01.git
cd roma-01

# Add upstream remote
git remote add upstream https://github.com/lukema95/roma-01.git
```

### Backend Setup

```bash
cd backend

# Create virtual environment
python3.13 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Install development dependencies
pip install pytest pytest-cov black isort mypy

# Copy environment template
cp .env.example .env
# Edit .env with your test credentials
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment template
cp .env.example .env.local

# Start development server
npm run dev
```

### Run Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

---

## Pull Request Process

### 1. Create a Branch

```bash
# Update your fork
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

**Branch Naming:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation only
- `refactor/` - Code refactoring
- `test/` - Adding tests
- `perf/` - Performance improvements

### 2. Make Your Changes

- Write clean, readable code
- Follow style guidelines (see below)
- Add tests for new features
- Update documentation as needed
- Keep commits atomic and well-described

### 3. Test Your Changes

```bash
# Run all tests
cd backend && pytest
cd frontend && npm test

# Check code style
cd backend
black --check .
isort --check .
mypy src/

cd frontend
npm run lint
```

### 4. Commit Your Changes

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git add .

# Format: <type>(<scope>): <subject>
git commit -m "feat(trading): add support for Hyperliquid DEX"
git commit -m "fix(api): resolve race condition in order execution"
git commit -m "docs(readme): update installation instructions"
```

**Commit Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, missing semicolons, etc)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvement
- `test`: Adding tests
- `chore`: Maintenance tasks

### 5. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Go to GitHub and create a Pull Request
```

**PR Checklist:**
- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Added tests for new features
- [ ] Updated documentation
- [ ] No merge conflicts
- [ ] Commits are well-formatted
- [ ] PR description is clear

**PR Template:**
```markdown
## Description
Brief description of the changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## How Has This Been Tested?
Describe the tests you ran.

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review
- [ ] I have commented my code where needed
- [ ] I have updated the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix/feature works
- [ ] New and existing tests pass locally
```

### 6. Code Review

- Be responsive to feedback
- Make requested changes promptly
- Keep the discussion focused and professional
- Once approved, a maintainer will merge your PR

---

## Style Guidelines

### Python Code Style

We follow **PEP 8** with some modifications:

```bash
# Format code
black src/

# Sort imports
isort src/

# Type checking
mypy src/
```

**Key Points:**
- Line length: 100 characters (not 79)
- Use type hints for all function signatures
- Docstrings for all public classes/functions
- Use f-strings for string formatting
- Prefer async/await over callbacks

**Example:**
```python
async def get_market_price(symbol: str) -> float:
    """
    Fetch current market price for a trading pair.
    
    Args:
        symbol: Trading pair symbol (e.g., "BTCUSDT")
        
    Returns:
        Current market price
        
    Raises:
        HTTPException: If API request fails
    """
    response = await client.get(f"/api/price/{symbol}")
    return response.json()["price"]
```

### TypeScript/React Code Style

```bash
# Run linter
npm run lint

# Fix automatically
npm run lint:fix
```

**Key Points:**
- Use TypeScript strict mode
- Functional components with hooks
- Props interfaces defined
- Use camelCase for variables
- Use PascalCase for components

**Example:**
```typescript
interface AgentCardProps {
  agentId: string;
  balance: number;
  isRunning: boolean;
}

export function AgentCard({ agentId, balance, isRunning }: AgentCardProps) {
  const [expanded, setExpanded] = useState(false);
  
  return (
    <div className="agent-card">
      {/* Component content */}
    </div>
  );
}
```

### Git Commit Messages

- Use present tense ("add feature" not "added feature")
- Use imperative mood ("move cursor to..." not "moves cursor to...")
- Limit first line to 72 characters
- Reference issues and pull requests when relevant

```
feat(api): add WebSocket support for real-time updates

- Implement WebSocket endpoint for agent updates
- Add connection management and auto-reconnect
- Update frontend to use WebSocket for live data

Closes #123
```

### Documentation Style

- Use clear, concise language
- Include code examples
- Keep line length reasonable (80-100 chars)
- Use proper markdown formatting
- Add table of contents for long docs

---

## Adding New Features

### New LLM Provider

1. Add provider to `backend/src/ai01/agents/trading_agent.py`
2. Create example config in `backend/config/models/`
3. Add provider to documentation
4. Add logo to `frontend/public/logos/`
5. Add tests

### New Exchange

1. Create new toolkit in `backend/src/ai01/toolkits/`
2. Inherit from `BaseDEXToolkit`
3. Implement all required methods
4. Add configuration support
5. Add tests
6. Update documentation

### New Trading Pair

1. Add coin icon to `frontend/public/coins/`
2. Update `coinIcons.ts`
3. Add to model configs
4. Update documentation

---

## Testing Guidelines

### Backend Tests

```python
# backend/tests/test_risk_management.py
import pytest
from ai01.agents.trading_agent import check_single_trade_limit

def test_single_trade_limit_no_positions():
    """Test single trade limit when no positions exist."""
    assert check_single_trade_limit(
        amount=500,
        available=1000,
        has_positions=False
    )
    assert not check_single_trade_limit(
        amount=600,
        available=1000,
        has_positions=False
    )

def test_single_trade_limit_with_positions():
    """Test single trade limit when positions exist."""
    assert check_single_trade_limit(
        amount=300,
        available=1000,
        has_positions=True
    )
    assert not check_single_trade_limit(
        amount=400,
        available=1000,
        has_positions=True
    )
```

### Frontend Tests

```typescript
// frontend/tests/AgentCard.test.tsx
import { render, screen } from '@testing-library/react';
import { AgentCard } from '@/components/AgentCard';

describe('AgentCard', () => {
  it('renders agent name correctly', () => {
    render(
      <AgentCard
        agentId="test-agent"
        name="Test Agent"
        balance={1000}
        isRunning={true}
      />
    );
    
    expect(screen.getByText('Test Agent')).toBeInTheDocument();
  });
  
  it('shows running status', () => {
    render(<AgentCard {...props} isRunning={true} />);
    expect(screen.getByText(/running/i)).toBeInTheDocument();
  });
});
```

---

## Community

### Getting Help

- 📖 Read the [documentation](docs/)
- 🐛 GitHub Issues: [https://github.com/lukema95/roma-01/issues](https://github.com/lukema95/roma-01/issues)
- 💬 Discussions: [https://github.com/lukema95/roma-01/discussions](https://github.com/lukema95/roma-01/discussions)
- 📧 Email: lukema95@gmail.com

### Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Given credit in the changelog

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

**Thank you for contributing to ROMA-01! 🚀**

We appreciate your time and effort in making this project better for everyone.

