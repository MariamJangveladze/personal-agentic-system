"""The Telegram boundary must reject unknown chats before running an agent."""

from pathlib import Path

from personal_agentic_system.config import Settings
from personal_agentic_system.telegram_gateway import TelegramGateway


class FakeWorkflow:
    def create_draft(self, objective: str):
        raise AssertionError("Unauthorized requests must not reach the workflow")


def test_unknown_chat_is_rejected(tmp_path: Path) -> None:
    config = Settings(
        runs_path=tmp_path / "runs",
        telegram_bot_token="synthetic-test-token",
        telegram_allowed_chat_ids=(123,),
    )
    gateway = TelegramGateway(config=config, workflow=FakeWorkflow())

    assert gateway.handle_message(999, "/draft do something") == "Unauthorized chat."

