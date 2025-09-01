#!/usr/bin/env python3
import json
import sys
import os
from pathlib import Path
from datetime import datetime

def find_latest_session():
    sessions_dir = Path.home() / ".codex" / "sessions"
    jsonl_files = list(sessions_dir.glob("**/*.jsonl"))
    
    if not jsonl_files:
        return None
    
    latest = max(jsonl_files, key=lambda f: f.stat().st_mtime)
    return latest

def extract_context(session_file):
    messages = []
    
    with open(session_file, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    if data.get('type') == 'message' and data.get('content'):
                        role = data.get('role', '')
                        content = data.get('content', [])
                        
                        for item in content:
                            if item.get('type') == 'input_text':
                                text = item.get('text', '')
                                if text and not text.startswith('<environment_context'):
                                    messages.append({
                                        'role': role,
                                        'text': text[:500]  # Limit length
                                    })
                except json.JSONDecodeError:
                    continue
    
    return messages

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--list':
        sessions_dir = Path.home() / ".codex" / "sessions"
        jsonl_files = sorted(sessions_dir.glob("**/*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
        
        print("Recent sessions:")
        for i, f in enumerate(jsonl_files[:10], 1):
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            print(f"{i}. {f.name} - {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        return
    
    latest = find_latest_session()
    
    if not latest:
        print("No session files found")
        return
    
    print(f"Loading session: {latest.name}")
    print(f"Modified: {datetime.fromtimestamp(latest.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    messages = extract_context(latest)
    
    if not messages:
        print("No messages found in session")
        return
    
    context_summary = []
    for msg in messages[-5:]:  # Last 5 messages
        role = "User" if msg['role'] == 'user' else "Assistant"
        text = msg['text'][:200] + "..." if len(msg['text']) > 200 else msg['text']
        context_summary.append(f"{role}: {text}")
    
    print("\nRecent context:")
    for item in context_summary:
        print(f"  {item}")
    
    print("\n" + "=" * 50)
    print("To continue with this context, use:")
    print(f"codex 'Continue from previous session about: [describe what you were working on]'")

if __name__ == "__main__":
    main()