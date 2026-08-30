"""Environment-backed configuration with safe local defaults."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    chat_model: str = os.getenv("OLLAMA_CHAT_MODEL", "qwen2.5:7b")
    embed_model: str = os.getenv("OLLAMA_EMBED_MODEL", "bge-m3")
    chroma_path: Path = Path(os.getenv("CHROMA_PATH", "storage/chroma"))
    chroma_collection: str = os.getenv(
        "CHROMA_COLLECTION", "personal_agentic_system"
    )
    vault_path: Path = Path(os.getenv("VAULT_PATH", "examples/vault"))
    runs_path: Path = Path(os.getenv("RUNS_PATH", "storage/runs"))
    api_host: str = os.getenv("API_HOST", "127.0.0.1")
    api_port: int = int(os.getenv("API_PORT", "8001"))
    api_control_token: str = os.getenv("API_CONTROL_TOKEN", "")
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_allowed_chat_ids: tuple[int, ...] = tuple(
        int(chat_id.strip())
        for chat_id in os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "").split(",")
        if chat_id.strip()
    )


settings = Settings()
