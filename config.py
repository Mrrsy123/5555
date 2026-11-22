"""
System Configuration & Telegram Credentials Manager
Supports both local JSON file and Cloud Environment Variables (Render/Heroku/Docker).
"""

import os
import json
from pathlib import Path

CONFIG_FILE = Path(__file__).resolve().parent / "telegram_config.json"

DEFAULT_CONFIG = {
    "telegram_bot_token": "",
    "telegram_chat_id": "",
    "min_confluence_score": 70,
    "scan_interval_seconds": 60,
    "assets": ["XAUUSD", "BTCUSD"],
    "timeframe": "15m"
}

def load_config() -> dict:
    cfg = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                cfg.update(saved)
        except Exception:
            pass

    # Override with Environment Variables if provided (for Cloud/Render deployment)
    env_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if env_token:
        cfg["telegram_bot_token"] = env_token.strip()

    env_chat = os.environ.get("TELEGRAM_CHAT_ID")
    if env_chat:
        cfg["telegram_chat_id"] = env_chat.strip()

    env_score = os.environ.get("MIN_CONFLUENCE_SCORE")
    if env_score:
        try:
            cfg["min_confluence_score"] = int(env_score)
        except Exception:
            pass

    env_interval = os.environ.get("SCAN_INTERVAL_SECONDS")
    if env_interval:
        try:
            cfg["scan_interval_seconds"] = int(env_interval)
        except Exception:
            pass

    return cfg

def save_config(cfg: dict) -> bool:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False
