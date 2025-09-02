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
    
    # Check if a specific session was selected
    selected_session = os.environ.get('CODEX_SELECTED_SESSION')
    if selected_session:
        matching_sessions = [Path(selected_session)]
        os.environ.pop('CODEX_SELECTED_SESSION')  # Clean up
    else:
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
        
        # Give codex instruction to read the file using Read tool
        line_count = resume_message.count(chr(10))
        chunks_needed = (line_count // 250) + 1
        
        instruction = f"""🔴 MANDATORY: Use Read tool to load session context 🔴

You MUST read this file using the Read tool: {context_file}

File info:
- Size: {len(resume_message):,} characters (~{len(resume_message)//4:,} tokens)  
- Lines: {line_count}
- Chunks needed: {chunks_needed} (at 250 lines each)

REQUIRED STEPS:
1. Use Read tool with parameters: file_path="{context_file}", offset=0, limit=250
2. Continue with offset=250, limit=250
3. Repeat until you've read all {line_count} lines

DO NOT USE:
- Shell commands (cat, head, tail, sed, dd)
- Any method other than Read tool

If you don't have Read tool, respond: "Read tool not available, please enable it."

After reading ALL chunks, acknowledge the full context is loaded."""
        
        subprocess.run(["codex", instruction])
    else:
        subprocess.run(["codex", resume_message])

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == '--list':
            # List available sessions
            current_dir = Path.cwd()
            matching = find_sessions_for_directory(current_dir)
            
            if matching:
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
                
                matching.sort(key=get_session_timestamp, reverse=True)
                print(f"\nSessions for {current_dir}:")
                for i, f in enumerate(matching[:10], 1):
                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                    size_mb = f.stat().st_size / 1024 / 1024
                    print(f"{i}. {f.name}")
                    print(f"   Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')} | Size: {size_mb:.2f} MB")
                print(f"\nTo resume a specific session with FULL context, use: codex-resume-full --session <number>")
            else:
                print(f"No sessions found for {current_dir}")
        
        elif sys.argv[1] == '--session' and len(sys.argv) > 2:
            # Resume specific session with full context
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
                                timestamp_part = timestamp_part.replace('T', ' ').replace('-', '')
                                return timestamp_part
                        except:
                            pass
                        return str(filepath.stat().st_mtime)
                    
                    matching.sort(key=get_session_timestamp, reverse=True)
                    
                    if 0 <= session_num < len(matching):
                        selected_session = matching[session_num]
                        print(f"Resuming session with FULL context: {selected_session.name}")
                        # Pass the selected session to main
                        sys.argv = [sys.argv[0]]  # Clear args
                        os.environ['CODEX_SELECTED_SESSION'] = str(selected_session)
                        main()
                    else:
                        print(f"Invalid session number. Available: 1-{len(matching)}")
                else:
                    print(f"No sessions found for {current_dir}")
            except ValueError:
                print("Invalid session number. Use: codex-resume-full --session <number>")
        
        elif sys.argv[1] == '--help':
            print("""Codex Resume Full - Continue sessions with COMPLETE context

DESCRIPTION:
  Loads entire session history including messages, tool calls, and outputs.
  This comprehensive version can load 250,000+ tokens of context.

USAGE:
  codex-resume-full              Resume the most recent session with full context
  codex-resume-full --list       List all available sessions for current directory
  codex-resume-full --session N  Resume specific session N with full context
  codex-resume-full --help       Show this help message

FEATURES:
  • Complete history: All messages, tool calls, and outputs
  • Large capacity: Handles up to ~250K+ tokens
  • Tool tracking: Includes bash commands, file edits, etc.
  • File-based loading: Uses ~/.codex/last-context.txt for large contexts
  • Read tool required: Forces use of Read tool for reliable loading

WHAT'S INCLUDED:
  ✓ User/Assistant messages (all)
  ✓ Tool calls (bash, edit, write, etc.)
  ✓ Tool outputs and results
  ✗ Encrypted reasoning blocks (not accessible)
  ✗ State metadata (filtered out)

EXAMPLES:
  codex-resume-full              # Resume last session with full context
  codex-resume-full --list       # Show sessions with sizes and timestamps
  codex-resume-full --session 3  # Load session #3 with complete history

READ TOOL REQUIREMENT:
  This script instructs Codex to use the Read tool for loading context.
  If Read tool is not available, Codex will notify you.
  The Read tool should auto-approve and not require multiple confirmations.

FILES:
  Sessions: ~/.codex/sessions/
  Temp context: ~/.codex/last-context.txt
  Script: /Users/btmacbookair/CascadeProjects/codex-resume-tool/

TOKEN USAGE:
  Typical session: 50K-250K tokens
  Large session: 250K-500K+ tokens
  
NOTE: For quick resume with lighter context (~8K tokens),
      use 'codex-resume' instead.
""")
        else:
            print(f"Unknown option: {sys.argv[1]}. Use --help for usage.")
    else:
        main()