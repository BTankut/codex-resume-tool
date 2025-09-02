#!/usr/bin/env python3
"""
Codex Resume Direct - Loads context directly without file reading
Avoids the chunking problem by sending context in batches
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

def extract_important_content(session_file, max_chars=80000):
    """Extract the most important content within size limit"""
    messages = []
    tool_summary = {"bash": 0, "edit": 0, "write": 0, "other": 0}
    
    with open(session_file, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        if line.strip():
            try:
                data = json.loads(line)
                record_type = data.get('type') or data.get('record_type')
                
                # Count tool usage
                if record_type == 'function_call':
                    tool_name = data.get('name', 'other')
                    if tool_name in tool_summary:
                        tool_summary[tool_name] += 1
                    else:
                        tool_summary["other"] += 1
                
                # Extract messages
                if record_type == 'message':
                    role = data.get('role', '')
                    content = data.get('content', [])
                    
                    for item in content:
                        if item.get('type') == 'input_text' and role == 'user':
                            text = item.get('text', '')
                            if text and not text.startswith('<'):
                                messages.append(f"👤 BT: {text[:1000]}")
                        
                        elif item.get('type') == 'output_text' and role == 'assistant':
                            text = item.get('text', '')
                            if text:
                                messages.append(f"🤖 Codex: {text[:2000]}")
                
            except json.JSONDecodeError:
                continue
    
    # Build context within size limit
    context_parts = []
    context_parts.append("=== SESSION CONTEXT ===\n")
    
    # Add tool usage summary
    context_parts.append("📊 Tool Usage Summary:")
    for tool, count in tool_summary.items():
        if count > 0:
            context_parts.append(f"  • {tool}: {count} calls")
    context_parts.append("")
    
    # Add messages (prioritize recent ones)
    context_parts.append("💬 Conversation History:\n")
    
    current_size = len("\n".join(context_parts))
    
    # Add messages from end (most recent first)
    for msg in reversed(messages):
        msg_size = len(msg) + 2  # +2 for newline
        if current_size + msg_size < max_chars:
            context_parts.insert(-1, msg)  # Insert before the last line
            current_size += msg_size
        else:
            break
    
    # Reverse to get chronological order
    conversation_index = context_parts.index("💬 Conversation History:\n") + 1
    conversation_end = len(context_parts)
    context_parts[conversation_index:conversation_end] = reversed(context_parts[conversation_index:conversation_end])
    
    context_parts.append("\n=== END OF CONTEXT ===")
    context_parts.append("\n✋ Context loaded. What would you like to do next?")
    
    return "\n".join(context_parts)

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
    
    # Check if specific session requested
    selected_session = os.environ.get('CODEX_SELECTED_SESSION')
    if selected_session:
        latest = Path(selected_session)
        os.environ.pop('CODEX_SELECTED_SESSION')
    else:
        latest = matching_sessions[0]
    
    print(f"Loading session: {latest.name}")
    
    # Extract and format context
    context = extract_important_content(latest)
    
    print(f"Context size: {len(context):,} characters (~{len(context)//4:,} tokens)")
    print("Sending directly to Codex...")
    
    # Send directly as command line argument
    subprocess.run(["codex", context])

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == '--list':
            current_dir = Path.cwd()
            matching = find_sessions_for_directory(current_dir)
            
            if matching:
                def get_session_timestamp(filepath):
                    name = filepath.name
                    try:
                        if 'rollout-' in name:
                            timestamp_part = name.split('rollout-')[1][:19]
                            return timestamp_part.replace('T', ' ').replace('-', '')
                    except:
                        pass
                    return str(filepath.stat().st_mtime)
                
                matching.sort(key=get_session_timestamp, reverse=True)
                print(f"\nSessions for {current_dir}:")
                for i, f in enumerate(matching[:10], 1):
                    mtime = datetime.fromtimestamp(f.stat().st_size)
                    size_mb = f.stat().st_size / 1024 / 1024
                    print(f"{i}. {f.name}")
                    print(f"   Size: {size_mb:.2f} MB")
            else:
                print(f"No sessions found for {current_dir}")
        
        elif sys.argv[1] == '--session' and len(sys.argv) > 2:
            try:
                session_num = int(sys.argv[2]) - 1
                current_dir = Path.cwd()
                matching = find_sessions_for_directory(current_dir)
                
                if matching:
                    def get_session_timestamp(filepath):
                        name = filepath.name
                        try:
                            if 'rollout-' in name:
                                timestamp_part = name.split('rollout-')[1][:19]
                                return timestamp_part.replace('T', ' ').replace('-', '')
                        except:
                            pass
                        return str(filepath.stat().st_mtime)
                    
                    matching.sort(key=get_session_timestamp, reverse=True)
                    
                    if 0 <= session_num < len(matching):
                        os.environ['CODEX_SELECTED_SESSION'] = str(matching[session_num])
                        main()
                    else:
                        print(f"Invalid session number. Available: 1-{len(matching)}")
                else:
                    print(f"No sessions found for {current_dir}")
            except ValueError:
                print("Invalid session number")
        
        elif sys.argv[1] == '--help':
            print("""Codex Resume Direct - Load context directly without file reading

Usage:
  codex-resume-direct           Load last session directly
  codex-resume-direct --list    List available sessions
  codex-resume-direct --session N  Load session N
  codex-resume-direct --help    Show this help

This version:
- Sends context directly (no file reading)
- Optimized size (80K chars max)
- Includes tool usage summary
- No chunking issues
""")
        else:
            print(f"Unknown option: {sys.argv[1]}")
    else:
        main()