#!/usr/bin/env python3
"""
Verify Context - Check if full context was loaded
"""
import sys
from pathlib import Path

def verify_context_file():
    context_file = Path.home() / ".codex" / "last-context.txt"
    
    if not context_file.exists():
        print("❌ No context file found at ~/.codex/last-context.txt")
        return False
    
    with open(context_file, 'r') as f:
        content = f.read()
    
    lines = content.count('\n')
    chars = len(content)
    tokens = chars // 4
    
    print(f"📊 Context File Stats:")
    print(f"  • File: {context_file}")
    print(f"  • Size: {chars:,} characters")
    print(f"  • Lines: {lines:,}")
    print(f"  • Estimated tokens: {tokens:,}")
    
    # Check for key markers
    has_start = "=== FULL SESSION HISTORY ===" in content
    has_end = "=== END OF HISTORY ===" in content
    has_tools = "[TOOL:" in content
    has_outputs = "📤 Output:" in content
    
    print(f"\n✅ Content Verification:")
    print(f"  • Has session start: {'✓' if has_start else '✗'}")
    print(f"  • Has session end: {'✓' if has_end else '✗'}")
    print(f"  • Has tool calls: {'✓' if has_tools else '✗'}")
    print(f"  • Has tool outputs: {'✓' if has_outputs else '✗'}")
    
    # Count different record types
    user_count = content.count("👤 BT:")
    assistant_count = content.count("🤖 Codex:")
    tool_count = content.count("[TOOL:")
    output_count = content.count("📤 Output:")
    
    print(f"\n📈 Record Counts:")
    print(f"  • User messages: {user_count}")
    print(f"  • Assistant messages: {assistant_count}")
    print(f"  • Tool calls: {tool_count}")
    print(f"  • Tool outputs: {output_count}")
    
    if tokens < 50000:
        print(f"\n⚠️  WARNING: Context seems small ({tokens:,} tokens)")
        print("     Expected 50K-250K+ tokens for full context")
        print("     You might be missing content!")
    else:
        print(f"\n✅ Context size looks good ({tokens:,} tokens)")
    
    return True

if __name__ == "__main__":
    verify_context_file()