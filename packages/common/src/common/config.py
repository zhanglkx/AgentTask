"""多环境配置。

设计原则:
- 单一 Settings 类承载所有配置。
- env_prefix='AGENTTASK_',避免污染全局环境变量空间。
- 敏感字段（API key / DB password）用 SecretStr,日志输出不会泄漏。
- get_settings() 缓存单例,reload=True 用于测试与显式重载。
"""

from __future__ import annotations

import enum

from pydantic import Field, SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from .errors import ConfigError


class AppEnv(enum.StrEnum):
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class Settings(BaseSettings):
    """全局配置。所有字段都可通过 AGENTTASK_<UPPER_SNAKE> 环境变量覆盖。"""

    model_config = SettingsConfigDict(
        env_prefix="AGENTTASK_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # 应用元信息
    app_env: AppEnv = Field(default=AppEnv.DEV, description="运行环境 dev/staging/prod")
    log_level: str = Field(default="INFO", description="日志级别")

    # LLM provider 默认值与 keys
    default_llm_provider: str = Field(default="deepseek")
    deepseek_api_key: SecretStr | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    anthropic_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None
    ollama_base_url: str = "http://localhost:11434"

    # 工具
    tavily_api_key: SecretStr | None = None

    # Postgres
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "agenttask"
    postgres_password: SecretStr = SecretStr("agenttask_dev")  # pragma: allowlist secret
    postgres_db: str = "agenttask"

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_http_port: int = 6333
    qdrant_grpc_port: int = 6334

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # LangSmith / OTel（M4 启用,M1 仅占位）
    langsmith_api_key: SecretStr | None = None
    langsmith_project: str = "agent-task"
    otel_endpoint: str | None = None

    # 成本预算（USD,0 表示不限制）
    monthly_budget_usd: float = 0.0

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def postgres_dsn(self) -> str:
        password = self.postgres_password.get_secret_value()
        return (
            f"postgresql://{self.postgres_user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


_cached_settings: list[Settings] = []


def get_settings(*, reload: bool = False) -> Settings:
    """返回全局 Settings 单例。

    Args:
        reload: True 时清除缓存并重新加载（测试用）。

    Raises:
        ConfigError: 当环境变量值无法通过 pydantic 校验时。
    """
    if reload:
        _cached_settings.clear()
    if not _cached_settings:
        try:
            _cached_settings.append(Settings())
        except ValidationError as e:
            raise ConfigError(
                f"settings validation failed: {e}",
                context={"errors": e.errors()},
            ) from e
    return _cached_settings[0]


__all__ = ["AppEnv", "Settings", "get_settings"]
