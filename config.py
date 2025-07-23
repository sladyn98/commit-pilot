import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    
    filter_extra_ignore: str = Field(default="", alias="FILTER_EXTRA_IGNORE")
    max_prompt_tokens: int = Field(default=8000, alias="MAX_PROMPT_TOKENS")
    edge_telemetry: bool = Field(default=True, alias="EDGE_TELEMETRY")  
    
    
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", alias="OPENAI_MODEL")
    
    @property
    def extra_ignore_patterns(self) -> list[str]:
        if not self.filter_extra_ignore:
            return []
        return [pattern.strip() for pattern in self.filter_extra_ignore.split(",") if pattern.strip()]