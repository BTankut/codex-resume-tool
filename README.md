# Codex Resume Tool

A collection of Python scripts that enable session continuation for Anthropic's Codex CLI, similar to Claude's `--continue` feature.

## 🚀 Features

- **Session Persistence**: Continue previous Codex sessions with full context
- **Directory-Aware**: Automatically finds sessions for your current working directory
- **Multiple Modes**: Choose between lightweight or full context restoration
- **Token Efficient**: Smart loading with configurable token limits
- **Cross-Project**: Works across all your projects

## 📦 Installation

### Prerequisites
- Python 3.6+
- Codex CLI installed
- Unix-like environment (macOS/Linux)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/BTankut/codex-resume-tool.git
cd codex-resume-tool
```

2. Make scripts executable:
```bash
chmod +x *.py
```

3. Add aliases to your shell configuration (`~/.zshrc` or `~/.bashrc`):
```bash
echo 'alias codex-resume="python3 '$(pwd)'/codex-resume.py"' >> ~/.zshrc
echo 'alias codex-resume-full="python3 '$(pwd)'/codex-resume-full.py"' >> ~/.zshrc
echo 'alias codex-continue="python3 '$(pwd)'/codex-continue.py"' >> ~/.zshrc
source ~/.zshrc
```

## 🎯 Usage

### Quick Resume (Recommended)
Resume your last session with conversation history:
```bash
cd /your/project
codex-resume
```
- Loads last 30 messages (~8K tokens)
- Fast and efficient
- Perfect for continuing recent work

### Full Resume
Resume with complete session history including tool calls:
```bash
cd /your/project
codex-resume-full
```
- Loads all messages + tool calls + outputs
- Can handle up to 256K tokens
- Ideal for complex debugging sessions

### Session Viewer
View available sessions for current directory:
```bash
cd /your/project
codex-continue --list
```

## 🔧 How It Works

The tool parses Codex's session files stored in `~/.codex/sessions/` and:

1. **Identifies** sessions belonging to your current directory
2. **Extracts** conversation history and tool interactions
3. **Formats** the context appropriately
4. **Loads** it into a new Codex session

### Session Data Types

| Type | Description | Included in Resume | Included in Full |
|------|-------------|-------------------|------------------|
| Messages | User/Assistant conversations | ✅ | ✅ |
| Tool Calls | Function invocations | ❌ | ✅ |
| Tool Outputs | Function results | ❌ | ✅ |
| Reasoning | Thought processes | ❌ | ❌ (encrypted) |

## 📁 Project Structure

```
codex-resume-tool/
├── codex-resume.py         # Main resume script (lightweight)
├── codex-resume-full.py    # Full context resume
├── codex-continue.py       # Session viewer/selector
└── README.md              # This file
```

## ⚙️ Configuration

### Adjust Message Limit
Edit `codex-resume.py` line ~194:
```python
# Default: last 30 messages
recent_messages = messages[-30:]  # Change 30 to your preference
```

### Change Token Budget
Edit `codex-resume-full.py` line ~194:
```python
# Default: 32000 characters (~8K tokens)
token_budget = 32000  # Increase for more context
```

## 🐛 Troubleshooting

### "No sessions found"
- Ensure you're in the correct project directory
- Check if sessions exist: `ls ~/.codex/sessions/`

### Context not loading completely
- For large contexts, use `codex-resume-full`
- Check file was created: `cat ~/.codex/last-context.txt`

### Token limit exceeded
- Use `codex-resume` instead of full version
- Adjust token budget in the script

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by Claude's `--continue` feature
- Built for the Codex community
- Special thanks to Anthropic for Codex CLI

## 📊 Comparison with Native Features

| Feature | Claude --continue | Codex Resume Tool |
|---------|------------------|-------------------|
| Native Support | ✅ | ❌ (Script-based) |
| Session Recovery | Automatic | Manual command |
| Token Efficiency | Optimized | Configurable |
| Directory Aware | ✅ | ✅ |
| Tool History | ✅ | ✅ |
| Custom Filtering | ❌ | ✅ |

## 🔜 Roadmap

- [ ] Session merging across multiple sessions
- [ ] Intelligent context summarization
- [ ] Token usage preview before loading
- [ ] Interactive session selection
- [ ] Support for encrypted reasoning blocks
- [ ] Windows compatibility
- [ ] GUI interface

## 💡 Tips

- Use `codex-resume` for quick continuations
- Use `codex-resume-full` when you need complete context
- Clean old sessions periodically to improve performance
- Set up keyboard shortcuts for faster access

## 🐞 Known Issues

- Reasoning blocks are encrypted and cannot be restored
- Very long lines (>2000 chars) may be truncated
- Maximum context limited by Codex's token limits

## 📧 Contact

- GitHub: [@BTankut](https://github.com/BTankut)
- Issues: [GitHub Issues](https://github.com/BTankut/codex-resume-tool/issues)

---

**Note**: This is an unofficial tool. For official Codex support, please refer to [Anthropic's documentation](https://docs.anthropic.com/).