from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
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
_ollama_url: str | None = None


def init_kshell(url: str) -> Client:
    global _client, _ollama_url
    _client = Client()
    _client.connect(url, username="makeit", password="1234")
    
    console.print("[dim]1/4 Installing zstd, Ollama, & Cloudflared...[/dim]")
    install_cmd = (
        "export PATH=/usr/local/bin:/usr/bin:/bin:$PATH; "
        "if ! command -v ollama >/dev/null 2>&1 && [ ! -f /usr/local/bin/ollama ]; then "
        "  (apt-get update -y && apt-get install -y zstd) || (sudo apt-get update -y && sudo apt-get install -y zstd) || true; "
        "  curl -fsSL https://ollama.com/install.sh | sh; "
        "fi; "
        "if ! command -v cloudflared >/dev/null 2>&1 && [ ! -f /usr/local/bin/cloudflared ]; then "
        "  curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared; "
        "fi"
    )
    _client.execute(install_cmd)
    
    console.print("[dim]2/4 Starting Ollama Server & Cloudflare Tunnel...[/dim]")
    daemon_script = (
        "import subprocess, time, re, os, urllib.request\n"
        "os.makedirs('/root/.ollama', exist_ok=True)\n"
        "os.makedirs(os.path.expanduser('~/.ollama'), exist_ok=True)\n"
        "env = os.environ.copy()\n"
        "env['OLLAMA_HOST'] = '0.0.0.0:2345'\n"
        "env['PATH'] = '/usr/local/bin:/usr/bin:/bin:' + env.get('PATH', '')\n"
        "ollama_bin = '/usr/local/bin/ollama' if os.path.exists('/usr/local/bin/ollama') else 'ollama'\n"
        "cf_bin = '/usr/local/bin/cloudflared' if os.path.exists('/usr/local/bin/cloudflared') else 'cloudflared'\n"
        "subprocess.run('pkill -9 -f \"ollama serve\"', shell=True)\n"
        "time.sleep(1)\n"
        "f_ollama = open('/tmp/ollama.log', 'w')\n"
        "subprocess.Popen([ollama_bin, 'serve'], env=env, stdout=f_ollama, stderr=f_ollama, start_new_session=True)\n"
        "server_up = False\n"
        "for _ in range(20):\n"
        "    try:\n"
        "        with urllib.request.urlopen('http://127.0.0.1:2345/api/tags', timeout=2) as r:\n"
        "            if r.status == 200:\n"
        "                server_up = True\n"
        "                break\n"
        "    except Exception:\n"
        "        pass\n"
        "    time.sleep(1)\n"
        "if not server_up:\n"
        "    f_ollama.flush()\n"
        "    with open('/tmp/ollama.log', 'r') as f:\n"
        "        print('OLLAMA_FAILED:' + f.read()[-500:])\n"
        "else:\n"
        "    f_cf = open('/tmp/ollama_tunnel.log', 'w')\n"
        "    subprocess.Popen([cf_bin, 'tunnel', '--url', 'http://127.0.0.1:2345', '--no-autoupdate'], stdout=f_cf, stderr=f_cf, start_new_session=True)\n"
        "    tunnel_url = ''\n"
        "    for _ in range(25):\n"
        "        if os.path.exists('/tmp/ollama_tunnel.log'):\n"
        "            with open('/tmp/ollama_tunnel.log', 'r') as f:\n"
        "                content = f.read()\n"
        "                match = re.search(r'https://[-a-z0-9]+\\.trycloudflare\\.com', content)\n"
        "                if match:\n"
        "                    tunnel_url = match.group(0)\n"
        "                    break\n"
        "        time.sleep(1)\n"
        "    print('TUNNEL_URL:' + tunnel_url)\n"
    )
    b64_daemon = base64.b64encode(daemon_script.encode("utf-8")).decode("utf-8")
    b64_daemon_clean = "".join(b64_daemon.splitlines())
    remote_daemon_cmd = f"python3 -c \"import base64; exec(base64.b64decode('{b64_daemon_clean}').decode('utf-8'))\""
    
    stdout, stderr, code = _client.execute(remote_daemon_cmd)
    out_text = stdout.strip()
    
    if out_text.startswith("OLLAMA_FAILED:"):
        raise RuntimeError(f"Remote Ollama Serve Failure: {out_text[14:]}")
    
    match = re.search(r"https://[-a-z0-9]+\.trycloudflare\.com", out_text)
    if match:
        _ollama_url = match.group(0)
        console.print(f"[dim]Ollama Cloudflare Tunnel Active: {_ollama_url}[/dim]")
    else:
        _ollama_url = f"http://127.0.0.1:2345"
        console.print(f"[yellow]Fallback Tunnel URL: {_ollama_url}[/yellow]")
    
    console.print(f"[dim]3/4 Pulling model {config.DEFAULT_MODEL} (please wait)...[/dim]")
    pull_model_cmd = (
        "export PATH=/usr/local/bin:/usr/bin:/bin:$PATH; "
        "export OLLAMA_HOST=0.0.0.0:2345; "
        "OLLAMA_BIN=$(which ollama 2>/dev/null || find /usr -name ollama 2>/dev/null | head -n 1 || echo /usr/local/bin/ollama); "
        "$OLLAMA_BIN list | grep -q '" + config.DEFAULT_MODEL + "' || $OLLAMA_BIN pull " + config.DEFAULT_MODEL
    )
    _client.execute(pull_model_cmd)
    
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
    global _ollama_url
    if not _ollama_url:
        get_client()

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

    req_data = json.dumps(payload).encode("utf-8")
    endpoint = f"{_ollama_url}/api/chat"

    max_retries = 5
    resp_data = None
    for attempt in range(max_retries):
        req = urllib.request.Request(endpoint, data=req_data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                break
        except urllib.error.HTTPError as e:
            if e.code in (502, 503, 504) and attempt < max_retries - 1:
                time.sleep(2)
                continue
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ollama API Error ({e.code}): {err_body}")
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            raise RuntimeError(f"Failed to reach Ollama endpoint ({endpoint}): {e}")

    if not resp_data:
        raise RuntimeError(f"Empty response from Ollama endpoint ({endpoint})")

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
