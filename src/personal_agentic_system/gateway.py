"""Model gateway with explicit attribution for local Ollama generation."""

import time
from dataclasses import dataclass

import requests

from personal_agentic_system.config import Settings, settings


@dataclass(frozen=True)
class GenerationResult:
    """Normalized response returned by every future model adapter."""

    text: str
    provider: str
    model: str
    latency_ms: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost_usd: float = 0.0
    finish_reason: str | None = None


class OllamaGateway:
    """Local model adapter that records model, latency, tokens, and outcome."""

    provider = "ollama"

    def __init__(self, config: Settings = settings) -> None:
        self.config = config

    def generate(self, prompt: str) -> GenerationResult:
        started = time.perf_counter()
        response = requests.post(
            f"{self.config.ollama_url}/api/generate",
            json={
                "model": self.config.chat_model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=180,
        )
        response.raise_for_status()
        body = response.json()
        text = str(body.get("response", "")).strip()
        if not text:
            raise RuntimeError("Ollama returned an empty response")

        return GenerationResult(
            text=text,
            provider=self.provider,
            model=str(body.get("model") or self.config.chat_model),
            latency_ms=round((time.perf_counter() - started) * 1000),
            input_tokens=body.get("prompt_eval_count"),
            output_tokens=body.get("eval_count"),
            # Local inference has no provider API charge. Hardware attribution is separate.
            estimated_cost_usd=0.0,
            finish_reason=body.get("done_reason"),
        )
