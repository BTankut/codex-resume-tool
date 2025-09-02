#!/usr/bin/env python3
"""
Codex Resume Chunked - Loads context in manageable chunks
Avoids the Read tool requirement and approval issues
"""
import json
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime

def find_sessions_for_directory(current_dir):
    """Find sessions that were run in the current directory"""
    sessions_dir = Path.home() / ".codex" / "sessions"
    jsonl_files = list(sessions_dir.glob("**/*.jsonl"))
    
    matching_sessions = []
    
    for session_file in jsonl_files:
        with open(session_file, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        if data.get('type') == 'message':
                            content = data.get('content', [])
                            for item in content:
                                text = item.get('text', '')
                                if '<cwd>' in text and str(current_dir) in text:
                                    matching_sessions.append(session_file)
                                    break
                    except json.JSONDecodeError:
                        continue
                if matching_sessions and matching_sessions[-1] == session_file:
                    break
    
    return matching_sessions

def extract_key_messages(session_file, max_messages=50):
    """Extract only the most important messages"""
    messages = []
    seen_instructions = False
    
    with open(session_file, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        if line.strip():
            try:
                data = json.loads(line)
                if data.get('type') == 'message':
                    role = data.get('role', '')
                    content = data.get('content', [])
                    
                    for item in content:
                        # User messages
                        if item.get('type') == 'input_text' and role == 'user':
                            text = item.get('text', '')
                            if text and not text.startswith('<'):
                                messages.append({
                                    'role': 'user',
                                    'text': text[:1000]  # Limit length
                                })
                        
                        # Assistant messages
                        elif item.get('type') == 'output_text' and role == 'assistant':
                            text = item.get('text', '')
                            if text:
                                messages.append({
                                    'role': 'assistant',
                                    'text': text[:1500]  # Limit length
                                })
                        
                        if len(messages) >= max_messages * 2:
                            break
                        
            except json.JSONDecodeError:
                continue
    
    # Return only the last N messages
    return messages[-max_messages:], seen_instructions

def main():
    current_dir = Path.cwd()
    print(f"Looking for sessions in: {current_dir}")
    
    matching_sessions = find_sessions_for_directory(current_dir)
    
    if not matching_sessions:
        print(f"No previous sessions found for this directory.")
        print("Starting fresh codex...")
        subprocess.run(["codex"])
        return
    
    # Get the most recent session
    def get_session_timestamp(filepath):
        name = filepath.name
        try:
            if 'rollout-' in name:
                timestamp_part = name.split('rollout-')[1][:19]
                timestamp_part = timestamp_part.replace('T', ' ').replace('-', '')
                return timestamp_part
        except:
            pass
        return str(filepath.stat().st_mtime)
    
    matching_sessions.sort(key=get_session_timestamp, reverse=True)
    latest = matching_sessions[0]
    
    print(f"\nFound {len(matching_sessions)} session(s)")
    print(f"Latest: {latest.name}")
    
    messages, has_instructions = extract_key_messages(latest)
    
    if not messages:
        print("No messages found. Starting fresh...")
        subprocess.run(["codex"])
        return
    
    print(f"Found {len(messages)} key messages")
    
    # Build context in a more digestible format
    context_parts = []
    
    context_parts.append("=== RESUMING PREVIOUS SESSION ===")
    context_parts.append("Here's a summary of our last conversation:")
    context_parts.append("")
    
    # Group messages for better readability
    for i, msg in enumerate(messages):
        if msg['role'] == 'user':
            context_parts.append(f"[{i+1}] You asked: {msg['text']}")
        else:
            context_parts.append(f"    I responded: {msg['text']}")
        context_parts.append("")
    
    context_parts.append("=== END OF CONTEXT ===")
    context_parts.append("")
    context_parts.append("Ready to continue. What would you like to do next?")
    
    resume_message = "\n".join(context_parts)
    
    # Check size and send directly
    if len(resume_message) > 50000:
        print(f"Context is large ({len(resume_message):,} chars), showing last 20 messages only")
        # Trim to last 20 messages
        messages = messages[-20:]
        context_parts = []
        context_parts.append("=== RECENT SESSION CONTEXT (TRIMMED) ===")
        for msg in messages:
            if msg['role'] == 'user':
                context_parts.append(f"You: {msg['text'][:500]}")
            else:
                context_parts.append(f"Me: {msg['text'][:500]}")
        context_parts.append("\n=== END ===\nReady to continue. What's next?")
        resume_message = "\n".join(context_parts)
    
    print(f"Starting codex with {len(resume_message):,} chars of context...")
    subprocess.run(["codex", resume_message])

if __name__ == "__main__":
    main()