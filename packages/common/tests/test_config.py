"""Settings 多环境配置测试。"""

from __future__ import annotations

import pytest

from common.config import AppEnv, Settings, get_settings
from common.errors import ConfigError


@pytest.mark.fast
def test_settings_defaults_are_sensible() -> None:
    """无任何环境变量时,Settings 应有合理默认值。"""
    s = Settings()
    assert s.app_env == AppEnv.DEV
    assert s.log_level == "INFO"
    assert s.default_llm_provider == "deepseek"
    assert s.postgres_host == "localhost"
    assert s.postgres_port == 5432
    assert s.qdrant_host == "localhost"
    assert s.qdrant_http_port == 6333
    assert s.redis_host == "localhost"
    assert s.redis_port == 6379


@pytest.mark.fast
def test_settings_reads_env_with_agenttask_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    """env_prefix=AGENTTASK_,AGENTTASK_APP_ENV=prod 应映射到 Settings.app_env=prod。"""
    monkeypatch.setenv("AGENTTASK_APP_ENV", "prod")
    monkeypatch.setenv("AGENTTASK_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("AGENTTASK_DEFAULT_LLM_PROVIDER", "anthropic")

    s = Settings()
    assert s.app_env == AppEnv.PROD
    assert s.log_level == "DEBUG"
    assert s.default_llm_provider == "anthropic"


@pytest.mark.fast
def test_settings_reads_provider_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    """API key 字段应可由环境变量注入并保持为 SecretStr。"""
    monkeypatch.setenv("AGENTTASK_DEEPSEEK_API_KEY", "sk-test-deepseek")
    monkeypatch.setenv("AGENTTASK_ANTHROPIC_API_KEY", "sk-ant-test")

    s = Settings()
    assert s.deepseek_api_key is not None
    assert s.deepseek_api_key.get_secret_value() == "sk-test-deepseek"
    assert s.anthropic_api_key is not None
    assert s.anthropic_api_key.get_secret_value() == "sk-ant-test"


@pytest.mark.fast
def test_settings_invalid_app_env_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """非法 AppEnv 值应抛 pydantic ValidationError(包装为 ConfigError 由 get_settings 处理)。"""
    monkeypatch.setenv("AGENTTASK_APP_ENV", "production")  # 应该是 prod
    with pytest.raises(ConfigError):
        get_settings(reload=True)


@pytest.mark.fast
def test_get_settings_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_settings() 默认缓存,多次调用返回同一实例。"""
    monkeypatch.setenv("AGENTTASK_LOG_LEVEL", "INFO")
    s1 = get_settings(reload=True)
    s2 = get_settings()
    assert s1 is s2


@pytest.mark.fast
def test_get_settings_reload_returns_new_instance(monkeypatch: pytest.MonkeyPatch) -> None:
    """reload=True 应清除缓存并返回新实例（用于测试切换环境）。"""
    monkeypatch.setenv("AGENTTASK_LOG_LEVEL", "INFO")
    s1 = get_settings(reload=True)
    monkeypatch.setenv("AGENTTASK_LOG_LEVEL", "DEBUG")
    s2 = get_settings(reload=True)
    assert s1 is not s2
    assert s2.log_level == "DEBUG"


@pytest.mark.fast
def test_redis_url_property() -> None:
    """Settings 应提供 redis_url 便捷属性,redis-py 直接消费。"""
    s = Settings()
    assert s.redis_url == "redis://localhost:6379/0"


@pytest.mark.fast
def test_postgres_dsn_property() -> None:
    """Settings 应提供 postgres_dsn 便捷属性。"""
    s = Settings()
    expected_start = "postgresql://agenttask:"
    expected_end = "@localhost:5432/agenttask"
    assert s.postgres_dsn.startswith(expected_start)
    assert s.postgres_dsn.endswith(expected_end)
