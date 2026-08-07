from __future__ import annotations

import argparse
import json
import os
import sys

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

if sys.platform == "win32":
    import ctypes
    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style

import config
from agent import llm
from agent.core import Agent

HOME_DIR = os.path.expanduser("~")

console = Console(highlight=False)

PROMPT_STYLE = Style.from_dict({
    "prompt": "ansibrightcyan bold",
    "": "ansiwhite",
})

LOGO_LINES = [
    "███╗   ███╗ █████╗ ██╗  ██╗███████╗    ██╗████████╗",
    "████╗ ████║██╔══██╗██║ ██╔╝██╔════╝    ██║╚══██╔══╝",
    "██╔████╔██║███████║█████╔╝ █████╗      ██║   ██║   ",
    "██║╚██╔╝██║██╔══██║██╔═██╗ ██╔══╝      ██║   ██║   ",
    "██║ ╚═╝ ██║██║  ██║██║  ██╗███████╗    ██║   ██║   ",
    "╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝    ╚═╝   ╚═╝   ",
]


def print_banner():
    console.print()
    console.print(Rule(style="cyan"))
    console.print()

    logo = Text(justify="left")
    for i, line in enumerate(LOGO_LINES):
        color = "bright_cyan" if i % 2 == 0 else "cyan"
        logo.append(line + "\n", style=f"bold {color}")

    console.print(logo)

    tagline = Text(justify="left")
    tagline.append("Terminal AI Agent", style="bold white")
    tagline.append("  •  ", style="dim cyan")
    tagline.append("Powered By KNI-ORG", style="bold cyan")
    tagline.append("  •  ", style="dim cyan")
    tagline.append("Free of cost", style="bold green")
    console.print()
    console.print(tagline)
    console.print()
    console.print(Rule(style="cyan"))
    console.print()

    info = Text(justify="left")
    info.append("WorkDir     : ", style="dim")
    info.append(config.WORKING_DIR, style="cyan")
    console.print(info)

    cmds = Text(justify="left")
    cmds.append("Commands    : ", style="dim")
    cmds.append("help  ·  clear  ·  exit", style="dim yellow")
    console.print(cmds)
    console.print()

    developer = Text(justify="left")
    developer.append("Developer   : ", style="dim")
    developer.append("Niranjan Kumar K", style="bold cyan")
    console.print(developer)

    project = Text(justify="left")
    project.append("Project     : ", style="dim")
    project.append("make_it - Terminal AI Coding Agent", style="bold white")
    console.print(project)
    console.print()


def print_help():
    console.print(Panel(
        "[bold]make it[/bold] — Terminal AI Coding Agent by [bold cyan]Kni-org[/bold cyan]\n\n"
        "[cyan]Built-in commands:[/cyan]\n"
        "  [yellow]help[/yellow]  [yellow]?[/yellow]        Show this help\n"
        "  [yellow]clear[/yellow]          Clear screen\n"
        "  [yellow]exit[/yellow]  [yellow]quit[/yellow]  [yellow]q[/yellow]  Exit\n\n"
        "[cyan]What you can ask:[/cyan]\n"
        '  "build a FastAPI REST API for a todo app with SQLite"\n'
        '  "create a CLI tool with click and typer"\n'
        '  "scaffold a Next.js + TypeScript project with Tailwind"\n'
        '  "write and run tests for main.py"\n'
        '  "find and fix the bug in app.py"\n'
        '  "set up Docker Compose with nginx + postgres + redis"\n'
        '  "refactor this project to use async/await throughout"\n\n'
        "[cyan]Navigation:[/cyan]\n"
        "  [dim]↑ / ↓ arrows[/dim]  Browse input history\n"
        "  [dim]→ arrow[/dim]       Accept auto-suggestion\n\n"
        "[cyan]Server URL:[/cyan]\n"
        "  Connected via kshell Cloudflare Tunnel.",
        title="[bold cyan]make it  ·  Kni-org[/bold cyan]",
        border_style="cyan",
    ))


def print_response(text: str):
    if not text.strip():
        return
    console.print()
    console.print(Rule(style="dim"))
    try:
        console.print(Markdown(text))
    except Exception:
        console.print(text)
    console.print(Rule(style="dim"))
    console.print()


def setup_kshell_url() -> str:
    console.print()
    console.print(Panel(
        "[bold yellow]Cloudflare Server URL Required[/bold yellow]\n\n"
        "[bold cyan]Note:[/bold cyan] Visit and follow instructions given at:\n"
        "[bold green]https://colab.research.google.com/github/hacker1514/make/blob/main/make_it.ipynb[/bold green]\n\n"
        "Paste the generated Cloudflare URL below to connect make_it.",
        title="[bold cyan]KShell Server Setup[/bold cyan]",
        border_style="cyan",
    ))
    console.print()

    while True:
        try:
            url = input("Cloudflare URL: ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[red]Setup cancelled.[/red]")
            sys.exit(1)

        if not url:
            console.print("[red]URL cannot be empty.[/red]")
            continue

        try:
            console.print("[bold blue]Connecting to kshell server...[/bold blue]")
            llm.init_kshell(url)

            with open(config.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"server_url": url}, f, indent=4)

            config.SERVER_URL = url
            console.print("\n[green]✓ Connected and initialized kshell server successfully.[/green]\n")
            return url
        except Exception as e:
            console.print(f"[red]Failed to connect to kshell server: {e}[/red]")


def run_repl(agent: Agent, initial_prompt: str | None = None):
    os.makedirs(config.SESSION_DIR, exist_ok=True)
    history_path = os.path.join(config.SESSION_DIR, "input_history.txt")
    session: PromptSession = PromptSession(
        history=FileHistory(history_path),
        auto_suggest=AutoSuggestFromHistory(),
        style=PROMPT_STYLE,
        mouse_support=False,
    )

    if initial_prompt:
        console.print(f"\n[bold cyan]▶[/bold cyan] [white]{initial_prompt}[/white]\n")
        response = agent.run(initial_prompt)
        print_response(response)

    while True:
        try:
            user_input = session.prompt(
                [("class:prompt", "\n◆ make it > ")],
            ).strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n\n[dim]Session saved. Goodbye.[/dim]\n")
            break

        if not user_input:
            continue

        lower = user_input.lower()

        if lower in ("exit", "quit", "q", ":q"):
            console.print("\n[dim]Session saved. Goodbye.[/dim]\n")
            break

        if lower in ("help", "?"):
            print_help()
            continue

        if lower == "clear":
            os.system("cls" if sys.platform == "win32" else "clear")
            continue

        console.print()
        try:
            response = agent.run(user_input)
            print_response(response)
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Enter a new prompt to continue.[/yellow]")
        except Exception as e:
            console.print(f"\n[red]Unexpected error: {e}[/red]")


def main():
    parser = argparse.ArgumentParser(
        prog="make_it",
        description="make it — Terminal AI Coding Agent by Kni-org",
    )
    parser.add_argument("prompt", nargs="?", help="Run a single prompt non-interactively")
    parser.add_argument("--version", action="version", version="make it  v1.0  ·  Kni-org")
    args = parser.parse_args()

    setup_kshell_url()
    print_banner()

    agent = Agent()

    if args.prompt:
        console.print(f"[bold cyan]▶[/bold cyan] [white]{args.prompt}[/white]\n")
        response = agent.run(args.prompt)
        print_response(response)
        agent.memory.save()
    else:
        run_repl(agent)


if __name__ == "__main__":
    main()
