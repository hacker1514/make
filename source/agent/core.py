from __future__ import annotations

import json
import os
import sys
from typing import Any

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.text import Text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from agent import llm, tools
from agent.memory import Memory

console = Console()

_TOOL_ICONS = {
    "read_file":    "📖",
    "write_file":   "✏️ ",
    "edit_file":    "🔧",
    "append_file":  "➕",
    "list_dir":     "📁",
    "create_dir":   "📂",
    "delete_file":  "🗑️ ",
    "move_file":    "📦",
    "copy_file":    "🗐 ",
    "run_command":  "⚡",
    "search_web":   "🔍",
    "get_file_info":"ℹ️ ",
    "find_in_files":"🔎",
    "patch_json":   "🗄️ ",
}


def _tool_label(name: str, args: dict) -> str:
    icon = _TOOL_ICONS.get(name, "🔨")
    match name:
        case "write_file":
            return f"  [bold cyan]{icon} WRITE[/bold cyan]  [white]{args.get('path', '')}[/white]"
        case "read_file":
            return f"  [bold cyan]{icon} READ[/bold cyan]   [white]{args.get('path', '')}[/white]"
        case "edit_file":
            return f"  [bold cyan]{icon} EDIT[/bold cyan]   [white]{args.get('path', '')}[/white]"
        case "append_file":
            return f"  [bold cyan]{icon} APPEND[/bold cyan] [white]{args.get('path', '')}[/white]"
        case "copy_file":
            return f"  [bold cyan]{icon} COPY[/bold cyan]   [white]{args.get('src', '')}[/white] → [white]{args.get('dst', '')}[/white]"
        case "move_file":
            return f"  [bold cyan]{icon} MOVE[/bold cyan]   [white]{args.get('src', '')}[/white] → [white]{args.get('dst', '')}[/white]"
        case "delete_file":
            return f"  [bold red]{icon} DELETE[/bold red] [white]{args.get('path', '')}[/white]"
        case "create_dir":
            return f"  [bold cyan]{icon} MKDIR[/bold cyan]  [white]{args.get('path', '')}[/white]"
        case "run_command":
            cmd = args.get("command", "")
            short = cmd if len(cmd) < 64 else cmd[:61] + "…"
            return f"  [bold yellow]{icon} EXEC[/bold yellow]   [bright_yellow]{escape(short)}[/bright_yellow]"
        case "search_web":
            return f"  [bold blue]{icon} SEARCH[/bold blue] [white]{escape(args.get('query', ''))}[/white]"
        case "find_in_files":
            return f"  [bold blue]{icon} FIND[/bold blue]   [white]{escape(args.get('pattern', ''))}[/white]"
        case "patch_json":
            return f"  [bold cyan]{icon} PATCH[/bold cyan]  [white]{args.get('path', '')}[/white] [{args.get('key_path', '')}]"
        case _:
            return f"  [bold magenta]{icon} {name.upper()}[/bold magenta]"


def _print_tool_result(name: str, raw: str):
    try:
        data = json.loads(raw)
    except Exception:
        data = raw

    if not isinstance(data, dict):
        return

    if "error" in data:
        console.print(f"     [bold red]✗ ERROR[/bold red] [dim]{escape(str(data['error']))}[/dim]")
        return

    if name == "run_command":
        rc = data.get("returncode", 0)
        stdout = (data.get("stdout") or "").strip()
        stderr = (data.get("stderr") or "").strip()
        status = "[bold green]✓ SUCCESS (exit 0)[/bold green]" if rc == 0 else f"[bold red]✗ FAILED (exit {rc})[/bold red]"
        console.print(f"     {status}")
        if stdout:
            lines = stdout.split("\n")
            shown = "\n     ".join(lines[:20])
            suffix = f"\n     [dim]… {len(lines) - 20} more lines[/dim]" if len(lines) > 20 else ""
            console.print(f"     [dim]{escape(shown)}[/dim]{suffix}")
        if stderr and rc != 0:
            lines = stderr.split("\n")
            console.print(f"     [dim red]{escape(chr(10).join(lines[:10]))}[/dim red]")
        return

    if name in ("write_file", "edit_file", "append_file", "create_dir",
                "move_file", "copy_file", "delete_file", "patch_json"):
        console.print("     [bold green]✓ COMPLETE[/bold green]")
        return

    if name == "read_file":
        lines = (data.get("content") or "").split("\n")
        console.print(f"     [dim]{escape(chr(10).join(lines[:6]))}[/dim]")
        return

    if name == "list_dir":
        keys = list((data.get("tree") or {}).keys())[:14]
        console.print(f"     [dim]{escape(', '.join(keys))}[/dim]")
        return

    if name == "search_web":
        for r in (data.get("results") or [])[:2]:
            snippet = (r.get("snippet") or "")[:120]
            console.print(f"     [dim]• {escape(snippet)}[/dim]")
        return

    if name == "find_in_files":
        total = data.get("total", 0)
        matches = data.get("matches", [])[:3]
        console.print(f"     [dim]{total} match(es)[/dim]")
        for m in matches:
            console.print(f"     [dim]{m['file']}:{m['line']}  {escape(m['text'][:80])}[/dim]")
        return


class Agent:
    def __init__(self):
        self.memory = Memory()

    def run(self, user_input: str) -> str:
        self.memory.add_user(user_input)
        self.memory.trim_if_needed()

        iterations = 0
        msg: dict = {}

        while iterations < config.MAX_ITERATIONS:
            iterations += 1

            with console.status("[bold bright_cyan]✦ AI Agent Processing...[/bold bright_cyan]", spinner="dots"):
                try:
                    msg = llm.chat_completion(
                        messages=self.memory.messages,
                        tools=tools.TOOL_SCHEMAS,
                    )
                except RuntimeError as e:
                    console.print(f"\n[red]{e}[/red]")
                    return str(e)
                except Exception:
                    console.print("\n[red]AI call failed[/red]")
                    return "AI call failed"

            self.memory.add_assistant(msg)

            tool_calls = msg.get("tool_calls")
            if not tool_calls:
                break

            for tc in tool_calls:
                fn_name = tc["function"]["name"]
                raw_args = tc["function"]["arguments"]
                tc_id = tc["id"]

                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except json.JSONDecodeError:
                    args = {}

                console.print(_tool_label(fn_name, args))
                result = tools.dispatch(fn_name, args)
                _print_tool_result(fn_name, result)
                self.memory.add_tool_result(tc_id, fn_name, result)

        self.memory.save()
        return msg.get("content", "")
