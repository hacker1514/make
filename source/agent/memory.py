from __future__ import annotations

import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class Memory:
    SYSTEM_PROMPT = """\
You are **make it** — a terminal AI coding agent built by Kni-org.
You have full access to the filesystem and shell of the user's machine.

Working Directory: {working_dir}

## MODE 1 — CONVERSATION
When the user sends a greeting, question, opinion, or general message (e.g. "hi", "how are you",
"what can you do", "explain X", "thanks") — respond naturally in plain text.
DO NOT call any tools. DO NOT create any files. Just reply like a helpful assistant.

## MODE 2 — BUILD / CODE TASK
When the user asks you to build, create, fix, run, install, scaffold, refactor, debug,
write code, or do anything that requires touching the filesystem or shell — switch to
full autonomous agent mode:

RULES for build mode:
1. Complete the task fully. Never stop halfway.
2. Use tools — actually call write_file, run_command etc. Never pretend or simulate.
3. Write real, working, production-quality code. Zero placeholders or TODOs.
4. After creating a project, verify it by running it. Fix any errors automatically.
5. If a package is missing, install it. If a command fails, read the error and retry.
6. Keep responses short and action-focused: ✓ created app.py  ✓ installed deps
7. After finishing, show the exact command(s) to run the result.
8. Use search_web when you need docs, package names, or best practices.

## DECIDING WHICH MODE
- "hi", "hello", "thanks", "what can you do", "how does X work" → MODE 1 (just chat)
- "build", "create", "make", "write", "fix", "run", "install", "scaffold", "add", "refactor" → MODE 2 (use tools)
- When unsure, ask one short clarifying question instead of assuming.
"""

    def __init__(self):
        self.messages: list[dict] = []
        self.working_dir = config.WORKING_DIR
        os.makedirs(config.SESSION_DIR, exist_ok=True)
        self.messages.append({
            "role": "system",
            "content": self.SYSTEM_PROMPT.format(working_dir=self.working_dir),
        })

    def add_user(self, text: str):
        self.messages.append({"role": "user", "content": text})

    def add_assistant(self, msg: dict):
        self.messages.append(msg)

    def add_tool_result(self, tool_call_id: str, name: str, content: str):
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": name,
            "content": content,
        })

    def trim_if_needed(self, max_messages: int = 100):
        if len(self.messages) <= max_messages:
            return
        system = self.messages[0]
        rest = self.messages[1:]
        self.messages = [system] + rest[-(max_messages - 1):]

    def save(self):
        try:
            sessions = []
            if os.path.exists(config.HISTORY_FILE):
                with open(config.HISTORY_FILE, encoding="utf-8") as f:
                    sessions = json.load(f)
            sessions.append({
                "timestamp": datetime.now().isoformat(),
                "working_dir": self.working_dir,
                "messages": self.messages,
            })
            sessions = sessions[-10:]
            with open(config.HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(sessions, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
