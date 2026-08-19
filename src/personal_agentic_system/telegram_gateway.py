"""Optional allowlisted Telegram gateway for the approval workflow."""

import logging
import time
from typing import Any

import requests

from personal_agentic_system.config import Settings, settings
from personal_agentic_system.workflow import ApprovalWorkflow

logger = logging.getLogger(__name__)


class TelegramGateway:
    """Accept a deliberately small command surface from approved chat IDs."""

    def __init__(
        self,
        config: Settings = settings,
        workflow: ApprovalWorkflow | None = None,
    ) -> None:
        if not config.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        if not config.telegram_allowed_chat_ids:
            raise ValueError("TELEGRAM_ALLOWED_CHAT_IDS must contain at least one chat ID")
        self.config = config
        self.workflow = workflow or ApprovalWorkflow(config=config)
        self.base_url = f"https://api.telegram.org/bot{config.telegram_bot_token}"

    def _request(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = requests.post(f"{self.base_url}/{method}", json=payload, timeout=60)
        response.raise_for_status()
        body = response.json()
        if not body.get("ok"):
            raise RuntimeError(f"Telegram API rejected {method}")
        return body

    def send(self, chat_id: int, text: str) -> None:
        self._request("sendMessage", {"chat_id": chat_id, "text": text[:4000]})

    def handle_message(self, chat_id: int, text: str) -> str:
        if chat_id not in self.config.telegram_allowed_chat_ids:
            logger.warning("Rejected Telegram request from non-allowlisted chat")
            return "Unauthorized chat."

        command, _, argument = text.strip().partition(" ")
        if command == "/draft" and argument.strip():
            record = self.workflow.create_draft(argument.strip())
            return (
                f"Draft {record.run_id} is awaiting approval.\n"
                f"Sources: {', '.join(record.sources) or 'none'}\n\n"
                f"{record.draft[:3200]}"
            )
        if command == "/approve" and argument.strip():
            run_id, _, reason = argument.strip().partition(" ")
            record = self.workflow.approve(run_id, f"telegram:{chat_id}", reason)
            return f"Approved {record.run_id}. Artifact: {record.artifact_path}"
        if command == "/reject" and argument.strip():
            run_id, _, reason = argument.strip().partition(" ")
            if not reason.strip():
                return "Usage: /reject <run-id> <reason>"
            record = self.workflow.reject(run_id, f"telegram:{chat_id}", reason)
            return f"Rejected {record.run_id}: {record.review_reason}"
        if command == "/metrics":
            return str(self.workflow.metrics())
        return (
            "Commands:\n/draft <objective>\n/approve <run-id> [reason]\n"
            "/reject <run-id> <reason>\n/metrics"
        )

    def run_forever(self) -> None:
        offset = 0
        while True:
            try:
                body = self._request(
                    "getUpdates", {"offset": offset, "timeout": 30, "allowed_updates": ["message"]}
                )
                for update in body.get("result", []):
                    offset = max(offset, int(update["update_id"]) + 1)
                    message = update.get("message", {})
                    chat_id = message.get("chat", {}).get("id")
                    text = message.get("text", "")
                    if isinstance(chat_id, int) and text:
                        self.send(chat_id, self.handle_message(chat_id, text))
            except requests.RequestException:
                logger.exception("Telegram polling failed; retrying")
                time.sleep(5)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    TelegramGateway().run_forever()


if __name__ == "__main__":
    main()

