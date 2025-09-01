#!/usr/bin/env python3
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

def extract_full_session(session_file):
    """Extract EVERYTHING from the session including tools and reasoning"""
    records = []
    seen_instructions = False
    
    with open(session_file, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        if line.strip():
            try:
                data = json.loads(line)
                record_type = data.get('type') or data.get('record_type')
                
                # Skip meta records
                if record_type in ['state', None]:
                    continue
                
                # Process messages
                if record_type == 'message':
                    role = data.get('role', '')
                    content = data.get('content', [])
                    
                    for item in content:
                        # User messages
                        if item.get('type') == 'input_text' and role == 'user':
                            text = item.get('text', '')
                            
                            # Filter out meta messages
                            if text and not text.startswith('<environment_context'):
                                if '<user_instructions>' in text:
                                    if not seen_instructions:
                                        seen_instructions = True
                                        records.append({
                                            'type': 'instruction',
                                            'text': '[Project configuration loaded]'
                                        })
                                elif '=== CONTEXT FROM PREVIOUS SESSION ===' not in text:
                                    records.append({
                                        'type': 'user',
                                        'text': text
                                    })
                        
                        # Assistant messages
                        elif item.get('type') == 'output_text' and role == 'assistant':
                            text = item.get('text', '')
                            if text:
                                records.append({
                                    'type': 'assistant',
                                    'text': text
                                })
                
                # Process tool calls
                elif record_type == 'function_call':
                    tool_name = data.get('name', 'unknown')
                    params = data.get('parameters', {})
                    
                    # Format tool call concisely
                    if tool_name == 'bash':
                        cmd = params.get('command', '')[:100]
                        records.append({
                            'type': 'tool_call',
                            'text': f"[TOOL: bash] {cmd}..."
                        })
                    elif tool_name == 'edit_file':
                        file = params.get('file_path', '')
                        records.append({
                            'type': 'tool_call', 
                            'text': f"[TOOL: edit] {file}"
                        })
                    else:
                        records.append({
                            'type': 'tool_call',
                            'text': f"[TOOL: {tool_name}]"
                        })
                
                # Process tool outputs
                elif record_type == 'function_call_output':
                    output = data.get('output', '')
                    if output:
                        # Don't truncate - keep full output
                        records.append({
                            'type': 'tool_output',
                            'text': output
                        })
                
                # Process reasoning
                elif record_type == 'reasoning':
                    # Reasoning might be encrypted, skip for now
                    summary = data.get('summary', '')
                    if summary and isinstance(summary, str):
                        records.append({
                            'type': 'reasoning',
                            'text': f"[THINKING] {summary}"
                        })
                        
            except json.JSONDecodeError:
                continue
    
    return records, seen_instructions

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
    print(f"File size: {latest.stat().st_size / 1024 / 1024:.2f} MB")
    
    records, has_instructions = extract_full_session(latest)
    
    if not records:
        print("No conversation found. Starting fresh...")
        subprocess.run(["codex"])
        return
    
    total_chars = sum(len(r['text']) for r in records)
    print(f"Found {len(records)} records (messages + tools + reasoning)")
    print(f"Total: ~{total_chars//4:,} tokens")
    
    # Build the full context
    context_parts = []
    
    context_parts.append("🔴 IMPORTANT: The following is your COMPLETE session history 🔴")
    context_parts.append("This includes all messages, tool calls, outputs, and reasoning.")
    context_parts.append("DO NOT re-execute old commands. Wait for my new instruction.")
    context_parts.append("")
    context_parts.append("=== FULL SESSION HISTORY ===\n")
    
    for record in records:
        if record['type'] == 'user':
            context_parts.append(f"👤 BT: {record['text']}")
        elif record['type'] == 'assistant':
            context_parts.append(f"🤖 Codex: {record['text']}")
        elif record['type'] == 'tool_call':
            context_parts.append(f"🔧 {record['text']}")
        elif record['type'] == 'tool_output':
            context_parts.append(f"📤 Output: {record['text']}")
        elif record['type'] == 'reasoning':
            context_parts.append(f"💭 {record['text']}")
        elif record['type'] == 'instruction':
            context_parts.append(f"📋 {record['text']}")
        context_parts.append("")
    
    context_parts.append("=== END OF HISTORY ===\n")
    context_parts.append("✋ Full context loaded. What would you like to do next?")
    
    resume_message = "\n".join(context_parts)
    
    print(f"\nFull context size: {len(resume_message):,} chars (~{len(resume_message)//4:,} tokens)")
    
    # Write to temp file if too large
    if len(resume_message) > 100000:  # If over 100K chars
        # Save to a known location
        context_file = Path.home() / ".codex" / "last-context.txt"
        context_file.parent.mkdir(exist_ok=True)
        
        with open(context_file, 'w') as f:
            f.write(resume_message)
        
        print(f"Context too large for command line ({len(resume_message):,} chars)")
        print(f"Saved to: {context_file}")
        print("Starting codex with file reading instruction...")
        
        # Give codex instruction to read the file
        instruction = f"""🔴 IMPORTANT: Read the ENTIRE session context 🔴

The file {context_file} contains {len(resume_message):,} characters (~{len(resume_message)//4:,} tokens).
It has {resume_message.count(chr(10))} lines.

Please read it COMPLETELY (you may need to read in chunks if there's a limit).

After reading ALL of it, acknowledge that you've loaded the full context and wait for my next instruction."""
        
        subprocess.run(["codex", instruction])
    else:
        subprocess.run(["codex", resume_message])

if __name__ == "__main__":
    main()