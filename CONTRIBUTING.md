# Contributing to Spending Tracker GUI

Thank you for your interest in contributing to Spending Tracker GUI! This document provides guidelines and information for contributors.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### Reporting Bugs

1. **Check existing issues** first to avoid duplicates
2. Use the **Bug Report** template when creating new issues
3. Include detailed steps to reproduce the issue
4. Provide your system information (OS, Python version, etc.)
5. Add screenshots if applicable

### Suggesting Features

1. **Check existing issues** for similar feature requests
2. Use the **Feature Request** template
3. Clearly describe the problem and proposed solution
4. Explain the use case and who would benefit
5. Consider alternative solutions

### Contributing Code

#### Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/spending-tracker-gui.git
   cd spending-tracker-gui
   ```
3. **Set up the development environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

#### Development Workflow

1. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes**:
   - Follow PEP8 style guidelines
   - Add docstrings for new functions/classes
   - Keep changes focused and atomic

3. **Test your changes**:
   ```bash
   # Run the application
   python src/main.py
   
   # Run tests (if available)
   python -m pytest tests/
   
   # Check code style
   flake8 src/
   black src/ --check
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add new expense category feature"
   ```

#### Commit Message Guidelines

Use conventional commit format:
- `feat:` new features
- `fix:` bug fixes
- `docs:` documentation changes
- `style:` code style changes
- `refactor:` code refactoring
- `test:` test additions or changes
- `chore:` maintenance tasks

#### Pull Request Process

1. **Push your branch** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request** on GitHub:
   - Use the PR template
   - Link to related issues
   - Provide clear description of changes
   - Add screenshots if UI changes are involved

3. **Code Review**:
   - Address feedback promptly
   - Make requested changes
   - Keep the PR updated with main branch

### Code Style Guidelines

#### Python Code Style

- Follow **PEP8** guidelines
- Use **type hints** where appropriate
- Maximum line length: **88 characters** (Black formatter standard)
- Use **docstrings** for functions, classes, and modules:
  ```python
  def calculate_total(expenses: List[Expense]) -> float:
      \"\"\"Calculate total amount from list of expenses.
      
      Args:
          expenses: List of expense objects
          
      Returns:
          Total amount as float
      \"\"\"
      return sum(expense.amount for expense in expenses)
  ```

#### GUI Code Guidelines

- Use **descriptive widget names**
- Separate UI logic from business logic
- Handle exceptions gracefully with user-friendly messages
- Ensure responsive design principles

#### Configuration

- Keep sensitive information out of code
- Use configuration files for settings
- Provide sensible defaults
- Document configuration options

### Testing

Currently, the project uses manual testing. We welcome contributions to add automated tests:

- **Unit tests** for individual functions/classes
- **Integration tests** for component interactions
- **GUI tests** for user interface functionality
- **End-to-end tests** for complete workflows

### Documentation

- Update **README.md** for new features
- Add **docstrings** to new code
- Update **configuration documentation** if needed
- Include **screenshots** for UI changes

### Development Environment

#### Recommended Tools

- **Python**: 3.8 or higher
- **IDE**: VS Code, PyCharm, or similar
- **Code Formatting**: Black
- **Linting**: Flake8
- **Version Control**: Git

#### Useful Commands

```bash
# Format code
black src/

# Lint code
flake8 src/

# Run application
python src/main.py

# Clean cache files
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
```

## Project Architecture

### Directory Structure

```
src/
├── config/         # Configuration management
├── controllers/    # Business logic
├── gui/           # PySide6 UI components
├── models/        # Data models
├── services/      # External integrations
└── main.py        # Application entry point
```

### Key Components

- **Config Manager**: Handles YAML configuration
- **Expense Controller**: Core business logic
- **Main Window**: Primary GUI interface
- **Google Sheets Service**: API integration
- **Email Service**: Report generation and sending

## Getting Help

- **Issues**: Use GitHub Issues for questions and bug reports
- **Discussions**: Use GitHub Discussions for general questions
- **Documentation**: Check README.md and inline documentation

## Recognition

Contributors will be acknowledged in the project README. We appreciate all forms of contribution, from code to documentation to issue reporting!

Thank you for contributing to Spending Tracker GUI! 🎉