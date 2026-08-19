"""Model gateway tests verify attribution without calling a real model."""

from unittest.mock import Mock, patch

from personal_agentic_system.config import Settings
from personal_agentic_system.gateway import OllamaGateway


@patch("personal_agentic_system.gateway.requests.post")
def test_ollama_gateway_attributes_tokens_and_model(post: Mock) -> None:
    post.return_value.json.return_value = {
        "response": "Drafted response",
        "model": "qwen2.5:7b",
        "prompt_eval_count": 42,
        "eval_count": 19,
        "done_reason": "stop",
    }
    post.return_value.raise_for_status.return_value = None

    result = OllamaGateway(Settings()).generate("Create a controlled draft")

    assert result.provider == "ollama"
    assert result.model == "qwen2.5:7b"
    assert result.input_tokens == 42
    assert result.output_tokens == 19
    assert result.estimated_cost_usd == 0.0
