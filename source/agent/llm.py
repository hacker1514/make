from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
from typing import Any

from rich.console import Console

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

console = Console()

def _ensure_kshell():
    try:
        import kshell
    except ImportError:
        console.print("[yellow]Installing kshell package...[/yellow]")
        subprocess.run([sys.executable, "-m", "pip", "install", "kshell"], check=True)

_ensure_kshell()
from kshell import Client

_client: Client | None = None


def init_kshell(url: str) -> Client:
    global _client
    _client = Client()
    _client.connect(url, username="makeit", password="1234")
    
    console.print("[dim]Checking Ollama installation...[/dim]")
    _client.execute("which ollama || curl -fsSL https://ollama.com/install.sh | sh")
    
    console.print("[dim]Ensuring Ollama server is running...[/dim]")
    _client.execute("pgrep -x ollama > /dev/null || (nohup ollama serve > /dev/null 2>&1 &)")
    
    console.print(f"[dim]Checking model {config.DEFAULT_MODEL}...[/dim]")
    _client.execute(f"ollama list | grep -q '{config.DEFAULT_MODEL}' || ollama pull {config.DEFAULT_MODEL}")
    
    return _client


def get_client() -> Client:
    global _client
    if _client is None:
        if config.SERVER_URL:
            init_kshell(config.SERVER_URL)
        else:
            raise RuntimeError("Cloudflare Server URL not initialized.")
    return _client


def _sanitize_messages(messages: list[dict]) -> list[dict]:
    clean: list[dict] = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content") or ""
        item: dict[str, Any] = {"role": role, "content": content}
        
        if "tool_calls" in m and m["tool_calls"]:
            clean_tc = []
            for tc in m["tool_calls"]:
                fn = tc.get("function", {})
                name = fn.get("name", "")
                raw_args = fn.get("arguments", {})
                if isinstance(raw_args, str):
                    try:
                        raw_args = json.loads(raw_args)
                    except Exception:
                        raw_args = {}
                clean_tc.append({
                    "function": {
                        "name": name,
                        "arguments": raw_args,
                    }
                })
            item["tool_calls"] = clean_tc
            
        clean.append(item)
    return clean


def chat_completion(
    messages: list[dict],
    tools: list[dict] | None = None,
) -> dict:
    client = get_client()
    clean_msgs = _sanitize_messages(messages)

    payload: dict[str, Any] = {
        "model": config.DEFAULT_MODEL,
        "messages": clean_msgs,
        "stream": False,
        "options": {
            "temperature": config.TEMPERATURE,
            "num_ctx": 4096,
        },
    }
    if tools:
        payload["tools"] = tools

    raw_json = json.dumps(payload)
    b64_payload = base64.b64encode(raw_json.encode("utf-8")).decode("utf-8")

    py_script = (
        "import base64, urllib.request, urllib.error\n"
        f"payload = base64.b64decode('{b64_payload}')\n"
        "req = urllib.request.Request('http://127.0.0.1:11434/api/chat', data=payload, headers={'Content-Type': 'application/json'})\n"
        "try:\n"
        "    with urllib.request.urlopen(req, timeout=600) as r:\n"
        "        print(r.read().decode('utf-8'))\n"
        "except urllib.error.HTTPError as e:\n"
        "    print('HTTP_ERR:' + str(e.code) + ':' + e.read().decode('utf-8'))\n"
    )
    
    b64_script = base64.b64encode(py_script.encode("utf-8")).decode("utf-8")
    b64_script_clean = "".join(b64_script.splitlines())

    remote_cmd = f"python3 -c \"import base64; exec(base64.b64decode('{b64_script_clean}').decode('utf-8'))\""

    stdout, stderr, exit_code = client.execute(remote_cmd)
    out_text = stdout.strip()

    if out_text.startswith("HTTP_ERR:"):
        raise RuntimeError(f"Ollama API Error: {out_text}")

    if exit_code != 0 or not out_text:
        raise RuntimeError(f"Remote LLM execution failed: {stderr or stdout}")

    resp_data = json.loads(out_text)
    msg = resp_data.get("message", {})

    result: dict[str, Any] = {
        "role": "assistant",
        "content": msg.get("content") or "",
    }

    if "tool_calls" in msg and msg["tool_calls"]:
        tool_calls = []
        for idx, tc in enumerate(msg["tool_calls"]):
            fn = tc.get("function", {})
            args = fn.get("arguments", {})
            args_str = json.dumps(args) if isinstance(args, dict) else str(args)
            tool_calls.append({
                "id": f"call_{idx}",
                "type": "function",
                "function": {
                    "name": fn.get("name", ""),
                    "arguments": args_str,
                },
            })
        result["tool_calls"] = tool_calls

    return result
