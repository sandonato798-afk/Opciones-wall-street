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

import time

_state_lock = threading.Lock()
_last_synced_signatures = {}
_last_sync_times = {}
MIN_SYNC_INTERVAL_SEC = 300  # Máximo 1 sync a GitHub cada 5 minutos por archivo
VOLATILE_KEYS = {"last_update", "last_rsi_scanned", "last_execution", "timestamp", "pings", "current_price", "scan_time"}

def _get_signature(data_dict):
    if not isinstance(data_dict, dict):
        return str(data_dict)
    filtered = {k: v for k, v in data_dict.items() if k not in VOLATILE_KEYS}
    return json.dumps(filtered, sort_keys=True)

def _init_local_signatures():
    for f in ["rsi_opportunistic_state.json", "alpha_trade_state.json", "wheel_compounding_state.json", "reinvestment_state.json", "daytrade_state.json"]:
        path = os.path.join(os.path.dirname(__file__), f)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as fp:
                    with _state_lock:
                        _last_synced_signatures[f] = _get_signature(json.load(fp))
                        _last_sync_times[f] = time.time()
            except Exception:
                pass

_init_local_signatures()

def _async_sync(file_name, data_dict):
    token = get_token()
    if not token:
        return

    sig = _get_signature(data_dict)
    
    with _state_lock:
        if _last_synced_signatures.get(file_name) == sig:
            return  # Sin cambios reales de trading, no commitear

        now = time.time()
        if now - _last_sync_times.get(file_name, 0) < MIN_SYNC_INTERVAL_SEC:
            return  # Throttle: evitar ban de GitHub API
        
        # Reservar tiempo para evitar race conditions multiples
        _last_sync_times[file_name] = now

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
                with _state_lock:
                    _last_synced_signatures[file_name] = sig
                    _last_sync_times[file_name] = time.time()
                print(f"[CLOUD_PERSISTENCE] Estado {file_name} respaldado en GitHub (Trade/Position change).")
    except Exception as e:
        print(f"[CLOUD_PERSISTENCE] Warning al respaldar {file_name}: {e}")

def sync_state_to_github_async(file_name, data_dict):
    t = threading.Thread(target=_async_sync, args=(file_name, data_dict), daemon=True)
    t.start()

def load_state_from_github(file_name):
    # 1. Intentar descargar directamente desde Raw GitHub (funciona siempre, con o sin token)
    raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{file_name}?cache_bust={int(datetime.now().timestamp())}"
    try:
        req = urllib.request.Request(raw_url, headers={"User-Agent": "WallStreet-Options-Bot"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data:
                return data
    except Exception:
        pass

    # 2. Fallback a GitHub API si hay token configurado
    token = get_token()
    if token:
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
            pass

    return None