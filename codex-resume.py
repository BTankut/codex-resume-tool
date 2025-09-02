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

def extract_real_conversation(session_file):
    """Extract only real user-assistant conversation in chronological order"""
    messages = []
    seen_instructions = False
    
    # Read file line by line to maintain order
    with open(session_file, 'r') as f:
        lines = f.readlines()
    
    # Process in order
    for line in lines:
        if line.strip():
            try:
                data = json.loads(line)
                if data.get('type') == 'message':
                    role = data.get('role', '')
                    content = data.get('content', [])
                    
                    # Process each content item
                    message_text = None
                    
                    for item in content:
                        # User messages
                        if item.get('type') == 'input_text' and role == 'user':
                            text = item.get('text', '')
                            
                            # Filter out meta messages
                            if not text:
                                continue
                            if text.startswith('<environment_context'):
                                continue
                            if text.startswith('<user_instructions>'):
                                if not seen_instructions:
                                    seen_instructions = True
                                continue
                            if '=== CONTEXT FROM PREVIOUS SESSION ===' in text:
                                continue
                            if '=== PREVIOUS SESSION CONTEXT ===' in text:
                                continue
                            if '=== CONTINUING FROM PREVIOUS SESSION ===' in text:
                                continue
                            if '=== END OF CONTEXT ===' in text:
                                continue
                            if text.strip() == '[Project configuration and guidelines loaded]':
                                continue
                            if text.strip() == '[Project instructions provided]':
                                continue
                            if 'Project instructions already loaded' in text:
                                continue
                            if 'Continue from where we left off' in text:
                                continue
                            if 'Recent conversation:' in text:
                                continue
                            if 'This is for context only' in text:
                                continue
                            if 'I\'m ready to continue' in text:
                                continue
                            
                            message_text = text
                        
                        # Assistant messages (output_text type for Codex)
                        elif item.get('type') == 'output_text' and role == 'assistant':
                            text = item.get('text', '')
                            if text:
                                # Filter out auto-responses
                                if all(phrase not in text for phrase in [
                                    "I've got the project context loaded",
                                    "Ready to continue. What should I tackle next?",
                                    "Great—what do you want to enable",
                                    "I'll start by scanning",
                                    "Got it — I've reviewed the context"
                                ]):
                                    message_text = text
                    
                    # Add message if we have valid text
                    if message_text:
                        messages.append({
                            'role': 'user' if role == 'user' else 'assistant',
                            'text': message_text,
                            'timestamp': len(messages)
                        })
                        
            except json.JSONDecodeError:
                continue
    
    return messages, seen_instructions

def get_last_user_task(messages):
    """Find the last actual user request/task"""
    for msg in reversed(messages):
        if msg['role'] == 'user':
            # Skip very short messages that are likely confirmations
            if len(msg['text']) > 20:
                return msg['text']
    return None

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
    
    # Get the most recent session based on filename timestamp
    def get_session_timestamp(filepath):
        name = filepath.name
        try:
            # Extract timestamp from filename: rollout-YYYY-MM-DDTHH-MM-SS-uuid.jsonl
            if 'rollout-' in name:
                timestamp_part = name.split('rollout-')[1][:19]  # Get YYYY-MM-DDTHH-MM-SS
                # Convert to comparable format
                timestamp_part = timestamp_part.replace('T', ' ').replace('-', '')
                return timestamp_part
        except:
            pass
        return str(filepath.stat().st_mtime)
    
    # Sort and get the latest
    matching_sessions.sort(key=get_session_timestamp, reverse=True)
    latest = matching_sessions[0]
    
    print(f"\nAll sessions for this directory (most recent first):")
    for i, session in enumerate(matching_sessions[:3], 1):
        print(f"  {i}. {session.name}")
    
    print(f"Found {len(matching_sessions)} session(s) for this directory")
    print(f"Latest: {latest.name}")
    print(f"File size: {latest.stat().st_size} bytes")
    print(f"Modified: {datetime.fromtimestamp(latest.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
    
    messages, has_instructions = extract_real_conversation(latest)
    
    if not messages:
        print("No real conversation found. Starting fresh...")
        subprocess.run(["codex"])
        return
    
    print(f"Found {len(messages)} messages (user + assistant)")
    
    # Build the context message with VERY clear instructions
    context_parts = []
    
    context_parts.append("🔴 IMPORTANT: READ THIS FIRST 🔴")
    context_parts.append("The following is ONLY for context from our previous session.")
    context_parts.append("DO NOT execute any commands or take any actions based on this context.")
    context_parts.append("Just acknowledge the context and wait for my next instruction.")
    context_parts.append("")
    context_parts.append("=== CONTEXT FROM PREVIOUS SESSION ===\n")
    
    # Send ALL messages from the session
    context_parts.append("Full session history:")
    
    total_chars = sum(len(msg['text']) for msg in messages)
    print(f"Loading ENTIRE session: {len(messages)} messages (~{total_chars//4:,} tokens)")
    
    for msg in messages:
        if msg['role'] == 'user':
            context_parts.append(f"\n👤 BT: {msg['text']}")
        else:
            context_parts.append(f"\n🤖 Codex: {msg['text']}")
    
    context_parts.append("\n=== END OF CONTEXT ===\n")
    
    # Show the very last exchange as a clear reminder
    context_parts.append("📍 LAST EXCHANGE REMINDER:\n")
    
    # Get the actual last exchange
    last_user = None
    last_assistant = None
    
    # Find last user message
    for msg in reversed(messages):
        if msg['role'] == 'user' and not last_user:
            last_user = msg
            break
    
    # Find last assistant message
    for msg in reversed(messages):
        if msg['role'] == 'assistant' and not last_assistant:
            last_assistant = msg
            break
    
    if last_user:
        text = last_user['text']
        if len(text) > 500:
            text = text[:500] + "..."
        context_parts.append(f"Last BT Message: {text}")
    
    if last_assistant:
        text = last_assistant['text']
        if len(text) > 500:
            text = text[:500] + "..."
        context_parts.append(f"\nLast Codex Response: {text}")
    
    context_parts.append("\n" + "="*50)
    context_parts.append("\n✋ I've loaded the context from our previous session.")
    context_parts.append("What would you like me to do now?")
    
    resume_message = "\n".join(context_parts)
    
    print("\nStarting codex with previous context...")
    print("(Context loaded - codex will wait for your instruction)")
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
                print(f"\nTo resume a specific session, use: codex-resume --session <number>")
            else:
                print(f"No sessions found for {current_dir}")
        
        elif sys.argv[1] == '--session' and len(sys.argv) > 2:
            # Resume specific session
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
                        print(f"Resuming session: {selected_session.name}")
                        # Pass the selected session to main
                        sys.argv = [sys.argv[0]]  # Clear args
                        os.environ['CODEX_SELECTED_SESSION'] = str(selected_session)
                        main()
                    else:
                        print(f"Invalid session number. Available: 1-{len(matching)}")
                else:
                    print(f"No sessions found for {current_dir}")
            except ValueError:
                print("Invalid session number. Use: codex-resume --session <number>")
        
        elif sys.argv[1] == '--help':
            print("""Codex Resume - Continue previous Codex sessions with conversation history

DESCRIPTION:
  Loads previous Codex session conversations for the current directory.
  This lightweight version loads only user/assistant messages (~8K tokens).

USAGE:
  codex-resume              Resume the most recent session
  codex-resume --list       List all available sessions for current directory
  codex-resume --session N  Resume specific session number N from the list
  codex-resume --help       Show this help message

FEATURES:
  • Directory-aware: Only shows sessions from current working directory
  • Lightweight: Loads last ~30 messages (approx 8,000 tokens)
  • Smart filtering: Removes meta messages and duplicates
  • Clear context: Shows last exchange as reminder
  • No auto-execution: Instructs Codex to wait for your command

EXAMPLES:
  codex-resume              # Resume last session in current directory
  codex-resume --list       # Show all sessions with timestamps and sizes
  codex-resume --session 2  # Resume the 2nd session from the list

RELATED COMMANDS:
  codex-resume-full         # Load FULL context including tool calls (~250K+ tokens)
  codex-resume-full --list  # List sessions for full context loading
  codex-chunked             # Alternative lightweight loader

FILES:
  Sessions stored in: ~/.codex/sessions/
  Script location: /Users/btmacbookair/CascadeProjects/codex-resume-tool/

NOTE: For complete session history including tool calls and outputs,
      use 'codex-resume-full' instead (requires Read tool).
""")
        else:
            print(f"Unknown option: {sys.argv[1]}. Use --help for usage.")
    else:
        main()