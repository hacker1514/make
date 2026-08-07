import os
import json

DEFAULT_MODEL = "qwen2.5:3b"

MAX_TOKENS = 8192
TEMPERATURE = 0.2

AGENT_NAME = "make it"
ORG_NAME = "Kni-org"

MAX_ITERATIONS = 40

WORKING_DIR = os.getcwd()

HOME_DIR = os.path.expanduser("~")
SESSION_DIR = os.path.join(HOME_DIR, ".make_it")
HISTORY_FILE = os.path.join(SESSION_DIR, "history.json")
CONFIG_FILE = os.path.join(SESSION_DIR, "config.json")

os.makedirs(SESSION_DIR, exist_ok=True)

SERVER_URL = ""

if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            SERVER_URL = data.get("server_url", "")
    except Exception:
        SERVER_URL = ""