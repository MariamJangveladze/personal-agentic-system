"""Unit tests for deterministic memory preparation behavior."""

from personal_agentic_system.memory import MemoryStore


def test_chunk_preserves_all_paragraphs() -> None:
    text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    chunks = MemoryStore.chunk(text, size=35, overlap=5)

    joined = " ".join(chunks)
    assert "First paragraph." in joined
    assert "Second paragraph." in joined
    assert "Third paragraph." in joined

