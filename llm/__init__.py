from typing import Protocol

from config import Config
from llm.openai import OpenAIProvider


class LLMProvider(Protocol):
    def generate_commit(self, diff_summary: dict) -> str:
        ...


def get_provider(provider_name: str, config: Config) -> LLMProvider:
    if provider_name == "openai":
        return OpenAIProvider(config)
    else:
        raise ValueError(f"Unknown provider: {provider_name}")