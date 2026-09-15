# -*- coding: utf-8 -*-
import os
import json
import base64
import urllib.request
import urllib.error
import threading
from datetime import datetime

GITHUB_REPO = "sandonato798-afk/Opciones-wall-street"

def get_token():
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token.strip()
    token_file = os.path.join(os.path.dirname(__file__), ".github_token")
    if os.path.exists(token_file):
        try:
            with open(token_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
    return ""

def _async_sync(file_name, data_dict):
    token = get_token()
    if not token:
        return

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_name}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "WallStreet-Options-Bot"
    }

    sha = None
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as resp:
            info = json.loads(resp.read().decode())
            sha = info.get("sha")
    except Exception:
        pass

    content_str = json.dumps(data_dict, indent=2, ensure_ascii=False)
    content_b64 = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")

    payload = {
        "message": f"Auto-Sync Cloud State: {file_name} [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]",
        "content": content_b64
    }
    if sha:
        payload["sha"] = sha

    try:
        req_put = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="PUT")
        with urllib.request.urlopen(req_put, timeout=8) as resp:
            if resp.status in (200, 201):
                print(f"[CLOUD_PERSISTENCE] Estado {file_name} respaldado en GitHub.")
    except Exception as e:
        print(f"[CLOUD_PERSISTENCE] Warning al respaldar {file_name}: {e}")

def sync_state_to_github_async(file_name, data_dict):
    t = threading.Thread(target=_async_sync, args=(file_name, data_dict), daemon=True)
    t.start()

def load_state_from_github(file_name):
    token = get_token()
    if not token:
        return None

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_name}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "WallStreet-Options-Bot"
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as resp:
            info = json.loads(resp.read().decode())
            content_b64 = info.get("content", "")
            raw_data = base64.b64decode(content_b64).decode("utf-8")
            return json.loads(raw_data)
    except Exception:
        return None