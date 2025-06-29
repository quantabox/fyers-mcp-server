# Contributing to Fyers MCP Server

We welcome contributions to make this project even better! Here's how you can help.

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/quantabox/fyers-mcp-server.git
   cd fyers-mcp-server
   ```
3. **Set up development environment**:
   ```bash
   uv sync --dev
   ```

## 🛠️ Development Setup

### Prerequisites
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) for dependency management
- [Claude Desktop](https://claude.ai/download) for testing

### Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit with your Fyers credentials
vim .env

# Install dependencies
uv sync --dev
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=. --cov-report=html

# Type checking
uv run mypy fyers_mcp_complete.py
```

### Manual Testing
```bash
# Test MCP server directly
uv run python fyers_mcp_complete.py

# Test with Claude Desktop
# Follow the README instructions for Claude configuration
```

## 📝 Code Style

We use Python best practices:

- **Black** for code formatting
- **isort** for import sorting
- **mypy** for type checking
- **flake8** for linting

```bash
# Format code
uv run black .
uv run isort .

# Check types
uv run mypy fyers_mcp_complete.py

# Lint
uv run flake8
```

## 🔧 Adding New Features

### Adding MCP Tools

1. **Add the tool function** in `fyers_mcp_complete.py`:
   ```python
   @mcp.tool()
   def your_new_tool(param: str) -> str:
       """Your tool description.
       
       Args:
           param: Parameter description
       """
       try:
           # Your implementation
           return "✅ Success message"
       except Exception as e:
           return f"❌ Error: {str(e)}"
   ```

2. **Follow error handling patterns**:
   - Always check authentication first
   - Use try/catch blocks
   - Return user-friendly messages with ✅/❌ prefixes

3. **Test thoroughly**:
   - Test with valid inputs
   - Test error conditions
   - Test authentication failures

### Documentation Updates

- Update README.md with new tool descriptions
- Add usage examples
- Update the tool count in status section

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Steps to reproduce**
2. **Expected behavior**
3. **Actual behavior**
4. **Environment details** (OS, Python version, etc.)
5. **Relevant logs** (sanitize any sensitive info)

Use the GitHub issue template:

```markdown
## Bug Description
Brief description of the bug

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: 
- Python version:
- Fyers MCP Server version:
- Claude Desktop version:

## Logs
```
[paste relevant logs here]
```
```

## 💡 Feature Requests

We're interested in:

### High Priority
- **WebSocket real-time data** streaming
- **Advanced order types** (OCO, Iceberg, etc.)
- **Risk management** tools
- **Portfolio analytics** and reporting

### Medium Priority
- **Options chain** analysis tools
- **Technical indicators** integration
- **Backtesting** capabilities
- **Paper trading** mode

### Low Priority
- **Mobile notifications**
- **Custom dashboards**
- **Integration with other brokers**

When proposing features:
1. **Describe the use case**
2. **Explain the benefit**
3. **Provide implementation ideas** if possible
4. **Consider existing API limitations**

## 📋 Pull Request Process

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Follow code style guidelines
   - Add tests for new functionality
   - Update documentation

3. **Test thoroughly**:
   ```bash
   # Run all tests
   uv run pytest
   
   # Test with Claude Desktop
   # Manual verification
   ```

4. **Commit with clear messages**:
   ```bash
   git commit -m "feat: add new trading tool for options chain"
   ```

5. **Push and create PR**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create Pull Request** on GitHub with:
   - **Clear title** and description
   - **Reference any issues** it closes
   - **Screenshots** if applicable
   - **Testing instructions**

## 🔍 Code Review Guidelines

### For Contributors
- **Self-review** your code before submitting
- **Write clear commit messages**
- **Add comments** for complex logic
- **Update tests** for changes

### For Reviewers
- **Be constructive** and helpful
- **Check functionality** and security
- **Verify documentation** updates
- **Test the changes** locally if possible

## 🏗️ Architecture Notes

### Project Structure
```
fyers-mcp-server/
├── fyers_mcp_complete.py    # Main MCP server (keep this focused)
├── pyproject.toml          # Dependencies and metadata
├── .env.example           # Environment template
├── tests/                 # Test files
├── docs/                  # Additional documentation
└── scripts/              # Utility scripts
```

### Design Principles
- **Keep it simple**: Focus on core trading functionality
- **Error handling**: Always provide clear error messages
- **Security**: Never log sensitive information
- **Performance**: Optimize for Claude Desktop integration
- **Reliability**: Handle network failures gracefully

## 🔒 Security Considerations

- **Never commit** `.env` files or credentials
- **Sanitize logs** of sensitive information
- **Validate inputs** to prevent injection attacks
- **Use HTTPS** for all API calls
- **Handle rate limits** appropriately

## 📖 Documentation

- **README.md**: Main documentation
- **Code comments**: Explain complex logic
- **Docstrings**: Document all public functions
- **Examples**: Provide usage examples
- **CHANGELOG.md**: Track version changes

## 🤝 Community

- **Be respectful** and inclusive
- **Help others** learn and contribute
- **Share knowledge** and best practices
- **Follow the code of conduct**

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and ideas
- **Discord/Slack**: [Link if available]

## 🎯 Roadmap

See our [GitHub Projects](https://github.com/quantabox/fyers-mcp-server/projects) for current priorities and planned features.

Thank you for contributing to Fyers MCP Server! 🚀