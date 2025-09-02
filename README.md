# Codex Resume Tool

A comprehensive toolkit for continuing Anthropic Codex CLI sessions with full context preservation, similar to Claude's `--continue` feature.

## 🚀 Features

- **Session Persistence**: Continue previous Codex sessions with complete context
- **Directory-Aware**: Automatically finds sessions for your current working directory
- **Multiple Loading Strategies**: Choose optimal method based on your needs
- **Session Selection**: Resume any previous session, not just the latest
- **Context Verification**: Ensure full context is loaded correctly
- **Token Optimization**: Smart chunking and loading strategies
- **Tool History**: Preserves tool calls and outputs

## 📦 Installation

### Prerequisites
- Python 3.6+
- Codex CLI installed
- Unix-like environment (macOS/Linux)

### Quick Setup

1. Clone the repository:
```bash
git clone https://github.com/BTankut/codex-resume-tool.git
cd codex-resume-tool
```

2. Make scripts executable:
```bash
chmod +x *.py
```

3. Add all aliases at once:
```bash
cat >> ~/.zshrc << 'EOF'
# Codex Resume Tool Aliases
alias codex-resume="python3 $(pwd)/codex-resume.py"
alias codex-resume-full="python3 $(pwd)/codex-resume-full.py"
alias codex-direct="python3 $(pwd)/codex-resume-direct.py"
alias codex-chunked="python3 $(pwd)/codex-resume-chunked.py"
alias codex-verify="python3 $(pwd)/verify-context.py"
EOF
source ~/.zshrc
```

## 🎯 Available Commands

### 1. `codex-resume` - Lightweight Resume (Recommended for Quick Continue)
```bash
codex-resume              # Resume most recent session
codex-resume --list       # List all sessions for current directory
codex-resume --session 3  # Resume specific session #3
codex-resume --help       # Show detailed help
```
- **Token Usage**: ~8,000 tokens
- **Content**: Last 30 messages only
- **Speed**: Very fast
- **Use When**: Quick continuation of recent work

### 2. `codex-resume-full` - Complete Context Resume (For Critical Work)
```bash
codex-resume-full              # Resume with FULL context
codex-resume-full --list       # List sessions with sizes
codex-resume-full --session 2  # Load session #2 with full context
codex-resume-full --help       # Show detailed help
```
- **Token Usage**: 50,000-250,000+ tokens
- **Content**: ALL messages, tool calls, outputs
- **Loading**: Uses file reading (📖 tool) with optimized chunking
- **Use When**: Need complete history, calculations, tool outputs

### 3. `codex-direct` - Direct Loading (No File Reading)
```bash
codex-direct              # Load context directly
codex-direct --list       # List available sessions
codex-direct --session N  # Load specific session
```
- **Token Usage**: ~80,000 tokens
- **Content**: Optimized selection of important content
- **Speed**: Fast, no chunking issues
- **Use When**: File reading is problematic

### 4. `codex-chunked` - Smart Chunked Loading
```bash
codex-chunked    # Load with intelligent chunking
```
- **Token Usage**: ~50,000 tokens
- **Content**: Last 50 important messages
- **Use When**: Alternative lightweight option

### 5. `codex-verify` - Verify Context Loading
```bash
codex-verify    # Check if context was fully loaded
```
Run this in a separate terminal after loading context to verify:
- File size and location
- Line and token counts
- Content markers
- Tool call statistics

## 📊 Command Comparison

| Command | Tokens | Speed | Completeness | Best For |
|---------|--------|-------|--------------|----------|
| `codex-resume` | ~8K | ⚡⚡⚡ | Last 30 msgs | Quick work |
| `codex-resume-full` | 50K-250K+ | ⚡ | Everything | Critical work |
| `codex-direct` | ~80K | ⚡⚡ | Optimized | No file reading |
| `codex-chunked` | ~50K | ⚡⚡ | Smart selection | Alternative |

## 🔧 Session Management

### List Sessions
```bash
codex-resume --list
```
Shows:
- Session filenames with timestamps
- File sizes
- Modification times
- Session numbers for selection

### Select Specific Session
```bash
codex-resume --session 2        # Lightweight load of session #2
codex-resume-full --session 2   # Full load of session #2
```

### Verify Loading
After loading context, verify in Codex:
```
"How many lines did you read?"
"Did you find the END OF HISTORY marker?"
"Search for [TOOL: - how many occurrences?"
```

Or from another terminal:
```bash
codex-verify
```

## ⚙️ Advanced Configuration

### Adjust Token Limits

Edit `codex-resume.py`:
```python
recent_messages = messages[-30:]  # Change 30 to desired count
```

Edit `codex-resume-full.py`:
```python
optimal_chunk_size = 2000  # Increase for fewer read operations
```

### Optimize Chunk Size

The scripts use intelligent chunking:
- Default: 2000 lines per chunk (1-2 reads total)
- Codex default: 25 lines (40+ reads)
- Adjustable based on your needs

## 🐛 Troubleshooting

### "Read tool not available"
- Codex uses file reading capability (📖), not a "Read tool"
- Script automatically handles this

### Too many read operations
- Use `codex-direct` for direct loading
- Or increase `optimal_chunk_size` in scripts

### Context not complete
1. Run `codex-verify` to check
2. Look for start/end markers
3. Verify token count matches expected

### Session not found
- Ensure you're in the correct directory
- Check `~/.codex/sessions/` for files
- Use `--list` to see available sessions

## 📁 File Structure

```
codex-resume-tool/
├── codex-resume.py          # Lightweight resume (8K tokens)
├── codex-resume-full.py     # Full context resume (250K+ tokens)
├── codex-direct.py          # Direct loading without file reading
├── codex-chunked.py         # Smart chunked loading
├── verify-context.py        # Context verification tool
├── VERIFICATION.md          # Verification guide
├── README.md               # This file
└── LICENSE                 # MIT License
```

## 🔍 Context Verification

The tool includes multiple verification methods:

1. **Automatic**: Scripts report loading statistics
2. **Manual**: Ask Codex about loaded content
3. **External**: Use `codex-verify` command

### What's Included in Full Context

✅ **Included:**
- All user messages
- All assistant responses  
- Tool calls (bash, edit, write, etc.)
- Tool outputs and results
- Error messages

❌ **Not Included:**
- Encrypted reasoning blocks
- State metadata
- System messages

## 💡 Best Practices

1. **For day-to-day work**: Use `codex-resume` (fast, lightweight)
2. **For critical continuity**: Use `codex-resume-full` (complete context)
3. **Always verify**: Run `codex-verify` for important sessions
4. **Session selection**: Use `--list` to find the right session
5. **Monitor tokens**: Check token usage with `/status` in Codex

## 🚨 Important Notes

- **Token Limits**: Full sessions can use 250K+ tokens
- **Pro Account Recommended**: For large context loading
- **Directory Specific**: Sessions are filtered by working directory
- **No Auto-Execution**: Scripts instruct Codex to wait for commands

## 🤝 Contributing

Contributions welcome! Feel free to:
- Report issues
- Suggest improvements
- Submit pull requests

## 📝 License

MIT License - see [LICENSE](LICENSE) file

## 🙏 Acknowledgments

- Inspired by Claude's `--continue` feature
- Built for the Codex community
- Special thanks to Anthropic for Codex CLI

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/BTankut/codex-resume-tool/issues)
- **Author**: [@BTankut](https://github.com/BTankut)

---

**Latest Version**: 2.0.0  
**Last Updated**: December 2024