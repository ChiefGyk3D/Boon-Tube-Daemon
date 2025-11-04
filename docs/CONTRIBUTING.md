# Contributing to Boon-Tube-Daemon

Thank you for your interest in contributing! 🎉

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version)
- Relevant logs (remove API keys!)

### Suggesting Features

Feature requests are welcome! Please include:
- Clear description of the feature
- Use case / why it's needed
- Proposed implementation (if you have ideas)

### Pull Requests

1. **Fork** the repository
2. **Create a branch** for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** with clear, descriptive commits
4. **Test your changes** thoroughly
5. **Update documentation** if needed (README.md, code comments)
6. **Submit a pull request**

#### PR Guidelines

- Keep PRs focused on a single feature/fix
- Write clear commit messages
- Follow existing code style
- Add comments for complex logic
- Update README if adding new features
- Test with multiple platforms if possible

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/Boon-Tube-Daemon.git
cd Boon-Tube-Daemon

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development tools (optional)
pip install black flake8 pytest
```

### Code Style

- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings to functions/classes
- Keep functions focused and small
- Use type hints where helpful

Example:
```python
def check_for_new_video(self, username: Optional[str] = None) -> Tuple[bool, Optional[dict]]:
    """
    Check if there's a new video since last check.
    
    Args:
        username: Username to check
        
    Returns:
        Tuple of (is_new, video_data)
    """
    # Implementation
```

### Testing

Before submitting a PR:

1. Test with actual API credentials (or mock them)
2. Test error handling (invalid configs, API failures)
3. Check logs for errors/warnings
4. Test on Linux (primary target platform)

### Adding New Platforms

#### New Media Platform (e.g., Instagram, Twitch)

1. Create `Media/platform_name.py`
2. Inherit from `MediaPlatform` base class
3. Implement required methods:
   - `authenticate()`
   - `get_latest_video()`
   - `check_for_new_video()`
4. Add configuration to `.env.example`
5. Update `main.py` to initialize your platform
6. Add documentation to README.md

#### New Social Platform (e.g., Telegram, Slack)

1. Create `Social/platform_name.py`
2. Implement `authenticate()` and `post()` methods
3. Handle platform-specific formatting
4. Add configuration to `.env.example`
5. Update `main.py` to initialize your platform
6. Add documentation to README.md

### Documentation

Good documentation is essential! When adding features:

- Update README.md with setup instructions
- Add configuration examples to .env.example
- Include inline code comments for complex logic
- Add docstrings to all public functions/classes

### Questions?

Feel free to open an issue for questions or discussions!

## Code of Conduct

Be respectful and constructive. We're all here to learn and build cool stuff. 🚀

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
