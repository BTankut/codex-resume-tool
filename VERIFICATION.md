# Context Verification Guide

## During Codex Session

After running `codex-resume-full`, Codex should report:
- Total lines read (e.g., "Loaded all 1088 lines")
- Token count (e.g., "~89,814 tokens")
- Confirmation of start/end markers

## From Another Terminal

While Codex is running, open a new terminal and run:
```bash
codex-verify
```

This will show:
- File size and location
- Line count
- Token estimate
- Content verification (markers, tools, outputs)
- Record counts

## Manual Verification in Codex

You can also ask Codex directly:
```
Please verify the loaded context by checking:
1. How many lines did you read?
2. Did you find "=== FULL SESSION HISTORY ===" at the start?
3. Did you find "=== END OF HISTORY ===" at the end?
4. How many tool calls did you find?
```

## Red Flags 🚩

Watch out for:
- Less than expected lines (should match what script reported)
- Missing start/end markers
- Token count way below expected
- Codex saying it only read "samples" or "first X lines"

## Quick Check Commands

In Codex, you can ask:
```
Search for "[TOOL: bash]" in the loaded context - how many did you find?
```

Or:
```
What was the last user message in the loaded context?
```

These help verify Codex actually has the full context in memory.