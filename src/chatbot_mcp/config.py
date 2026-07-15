"""Settings - pydantic-settings with .env support."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    server_name: str = "chatbot-mcp"
    backend_port: int = Field(default=11101, alias="BACKEND_PORT")
    frontend_port: int = Field(default=11102, alias="FRONTEND_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    db_path: str = Field(default="data/chatbot.db", alias="DB_PATH")

    regulatory_regime: str = Field(default="none", alias="CHATBOT_REGULATORY_REGIME")
    real_name_auth: bool = Field(default=False, alias="CHATBOT_REAL_NAME_AUTH")
    conversation_retention_days: int = Field(default=90, alias="CHATBOT_RETENTION_DAYS")

    llm_provider: str = Field(default="local-llm-mcp", alias="CHATBOT_LLM_PROVIDER")
    llm_base_url: str = Field(default="http://127.0.0.1:10832", alias="CHATBOT_LLM_BASE_URL")
    llm_model: str = Field(default="", alias="CHATBOT_LLM_MODEL")

    speech_mcp_url: str = Field(default="http://127.0.0.1:10909", alias="CHATBOT_SPEECH_MCP_URL")
    avatar_mcp_url: str = Field(default="http://127.0.0.1:10792", alias="CHATBOT_AVATAR_MCP_URL")
    resonite_mcp_url: str = Field(
        default="http://127.0.0.1:10978", alias="CHATBOT_RESONITE_MCP_URL"
    )
    memops_url: str = Field(default="http://127.0.0.1:10732", alias="CHATBOT_MEMOPS_URL")

    safety_rate_limit_per_minute: int = Field(default=30, alias="CHATBOT_RATE_LIMIT")
    api_key: str = Field(default="", alias="CHATBOT_API_KEY")


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
