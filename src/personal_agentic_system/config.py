"""Environment-backed configuration with safe local defaults."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load the documented local file before the module-level settings object is built.
# Deployment environments can continue to inject variables normally.
load_dotenv()


def _allowed_chat_ids() -> tuple[int, ...]:
    return tuple(
        int(chat_id.strip())
        for chat_id in os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "").split(",")
        if chat_id.strip()
    )


@dataclass(frozen=True)
class Settings:
    ollama_url: str = field(
        default_factory=lambda: os.getenv("OLLAMA_URL", "http://localhost:11434")
    )
    chat_model: str = field(default_factory=lambda: os.getenv("OLLAMA_CHAT_MODEL", "qwen2.5:7b"))
    embed_model: str = field(default_factory=lambda: os.getenv("OLLAMA_EMBED_MODEL", "bge-m3"))
    chroma_path: Path = field(
        default_factory=lambda: Path(os.getenv("CHROMA_PATH", "storage/chroma"))
    )
    chroma_collection: str = field(
        default_factory=lambda: os.getenv("CHROMA_COLLECTION", "personal_agentic_system")
    )
    vault_path: Path = field(
        default_factory=lambda: Path(os.getenv("VAULT_PATH", "examples/vault"))
    )
    runs_path: Path = field(default_factory=lambda: Path(os.getenv("RUNS_PATH", "storage/runs")))
    api_host: str = field(default_factory=lambda: os.getenv("API_HOST", "127.0.0.1"))
    api_port: int = field(default_factory=lambda: int(os.getenv("API_PORT", "8001")))
    api_control_token: str = field(default_factory=lambda: os.getenv("API_CONTROL_TOKEN", ""))
    telegram_bot_token: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    telegram_allowed_chat_ids: tuple[int, ...] = field(default_factory=_allowed_chat_ids)


settings = Settings()
