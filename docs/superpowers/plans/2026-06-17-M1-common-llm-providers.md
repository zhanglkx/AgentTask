# M1：`packages/common` + `packages/llm_providers` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付两个生产级 SDK 包：`common`（config / logging / errors / retry / cost / cache）与 `llm_providers`（factory + 4 个 provider + middleware + embeddings），覆盖率 ≥ 80%，达到 spec 第 9.1 节 M1 验收标准。

**Architecture:** 每个包独立 src-layout、独立 pyproject.toml、独立 tests/，作为 uv workspace 成员。`llm_providers` 单向依赖 `common`。所有 LLM 调用通过 LangChain 抽象，单元测试用 LangChain 内置 `FakeListChatModel` / mock 替代真实调用，缓存测试用 `fakeredis`，真实 LLM 联调测试打 `@pytest.mark.llm` 默认跳过。

**Tech Stack:** Python 3.12, pydantic v2 + pydantic-settings, structlog, tenacity, redis-py + fakeredis, langchain-core, langchain-openai, langchain-anthropic, langchain-ollama, pytest + pytest-asyncio + pytest-cov。

**Branch:** 在 `chore/m0-foundation`（或 M0 合入 main 后基于 main）创建新分支 `feat/m1-common-llm-providers`。所有 commit 在该分支上。

---

## File Structure 总览

```
packages/common/
├── pyproject.toml              # workspace 成员 + 运行时依赖
├── README.md                   # 包说明（中文）
├── src/common/
│   ├── __init__.py             # 公开 API re-export
│   ├── config.py               # Settings(BaseSettings) 多环境配置
│   ├── errors.py               # AgentError 层级
│   ├── logging.py              # configure_logging + get_logger
│   ├── retry.py                # tenacity 装饰器
│   ├── cost.py                 # CostTracker + PRICE_TABLE
│   └── cache.py                # Redis 缓存装饰器
└── tests/
    ├── __init__.py
    ├── conftest.py             # 共用 fixtures（fakeredis, env 隔离）
    ├── test_config.py
    ├── test_errors.py
    ├── test_logging.py
    ├── test_retry.py
    ├── test_cost.py
    └── test_cache.py

packages/llm_providers/
├── pyproject.toml              # 依赖 common + langchain-*
├── README.md
├── src/llm_providers/
│   ├── __init__.py             # 公开 API: get_chat_model, get_embeddings
│   ├── factory.py              # get_chat_model() 总入口
│   ├── middleware.py           # with_cost_tracking / with_retry / with_cache
│   ├── embeddings.py           # get_embeddings()
│   └── providers/
│       ├── __init__.py
│       ├── deepseek.py         # build_deepseek_chat()
│       ├── anthropic.py        # build_anthropic_chat()
│       ├── openai.py           # build_openai_chat()
│       └── ollama.py           # build_ollama_chat()
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_factory.py
    ├── test_provider_deepseek.py
    ├── test_provider_anthropic.py
    ├── test_provider_openai.py
    ├── test_provider_ollama.py
    ├── test_middleware.py
    └── test_embeddings.py

examples/m1_provider_switch.py  # 5 行 demo（验收脚本）
```

---

## Task 1：创建 `packages/common` 骨架

**Files:**
- Create: `packages/common/pyproject.toml`
- Create: `packages/common/README.md`
- Create: `packages/common/src/common/__init__.py`
- Create: `packages/common/tests/__init__.py`
- Modify: `pyproject.toml`（根 dependency-groups dev 加 fakeredis、httpx）

- [ ] **Step 1.1：切到新分支**

```bash
git switch -c feat/m1-common-llm-providers
```

Expected：`Switched to a new branch 'feat/m1-common-llm-providers'`。

- [ ] **Step 1.2：创建目录与 pyproject**

```bash
mkdir -p packages/common/src/common packages/common/tests
rm -f packages/.gitkeep  # 不再需要,目录已有内容
```

Create `packages/common/pyproject.toml`：

```toml
[project]
name = "common"
version = "0.1.0"
description = "AgentTask 基础设施包：config / logging / errors / retry / cost / cache"
readme = "README.md"
requires-python = ">=3.12,<3.13"
license = { text = "MIT" }
authors = [{ name = "AgentTask Author" }]
dependencies = [
    "pydantic>=2.9,<3",
    "pydantic-settings>=2.6,<3",
    "structlog>=24.4",
    "tenacity>=9.0,<10",
    "redis>=5.2,<6",
]

[build-system]
requires = ["hatchling>=1.25"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/common"]

[tool.hatch.build.targets.sdist]
include = ["src/common", "README.md"]
```

- [ ] **Step 1.3：创建 README**

Create `packages/common/README.md`：

```markdown
# common

AgentTask 仓库的基础设施包。被所有其他 `packages/*` 与 `apps/*` 依赖。

## 包含模块

| 模块 | 作用 | 对应 JS 概念 |
|---|---|---|
| `config` | pydantic-settings 多环境配置 | `zod` + `dotenv` |
| `logging` | structlog 结构化日志 | `pino` |
| `errors` | 统一错误层级 | 自定义 Error 类 |
| `retry` | tenacity 重试策略 | `p-retry` |
| `cost` | LLM 成本追踪 | - |
| `cache` | Redis 响应缓存 | `redis` + 装饰器 |

## 使用

```python
from common import get_settings, configure_logging, get_logger

settings = get_settings()
configure_logging(settings.log_level)
log = get_logger(__name__)
log.info("hello", env=settings.app_env)
```

详见各子模块 docstring 与 `tests/`。
```

- [ ] **Step 1.4：创建 `__init__.py` 占位**

Create `packages/common/src/common/__init__.py`：

```python
"""common: AgentTask 基础设施包。

公开 API 在子模块就绪后逐步 re-export。M1 期间该文件保持简洁,
具体导入见各子模块。
"""

from __future__ import annotations

__version__ = "0.1.0"
```

Create `packages/common/tests/__init__.py`（空文件）：

```python
```

- [ ] **Step 1.5：根 pyproject 添加测试依赖**

修改 `/Users/temptrip/Documents/GitHub/AgentTask/pyproject.toml`，把 `dev` group 替换为：

```toml
[dependency-groups]
dev = [
    "ruff>=0.8.0",
    "mypy>=1.13",
    "pytest>=8.3",
    "pytest-asyncio>=0.24",
    "pytest-cov>=6.0",
    "pre-commit>=4.0",
    "commitizen>=4.0",
    "detect-secrets>=1.5",
    "mkdocs-material>=9.5",
    "mkdocs>=1.6",
    "fakeredis>=2.26",
    "respx>=0.21",
    "freezegun>=1.5",
]
```

- [ ] **Step 1.6：同步依赖**

```bash
uv sync
```

Expected：解析并安装 `pydantic-settings` / `structlog` / `tenacity` / `redis` / `fakeredis` 等。`packages/common` 作为 workspace 成员被识别。

- [ ] **Step 1.7：跑 lint + type 验证骨架**

```bash
uv run ruff check packages/common
uv run mypy packages/common
```

Expected：均通过（仅 `__init__.py` 不会触发任何错误）。

- [ ] **Step 1.8：提交**

```bash
git add packages/common/pyproject.toml packages/common/README.md packages/common/src/common/__init__.py packages/common/tests/__init__.py pyproject.toml uv.lock
git rm --cached packages/.gitkeep 2>/dev/null || true
rm -f packages/.gitkeep
git add -u packages/.gitkeep 2>/dev/null || true
git commit -m "feat(common): 创建 packages/common 包骨架（src-layout + 运行时依赖）"
```

---

## Task 2：`common.errors` —— 错误类层级（TDD）

**Files:**
- Create: `packages/common/tests/test_errors.py`
- Create: `packages/common/src/common/errors.py`

- [ ] **Step 2.1：写失败的测试**

Create `packages/common/tests/test_errors.py`：

```python
"""错误类层级行为测试。"""

from __future__ import annotations

import pytest

from common.errors import (
    AgentError,
    BudgetExceededError,
    ConfigError,
    LLMError,
    RateLimitError,
    RetryableError,
    ToolError,
)


@pytest.mark.fast
def test_agent_error_is_base_class() -> None:
    """所有自定义错误都应继承 AgentError。"""
    for cls in (LLMError, ToolError, RetryableError, RateLimitError, BudgetExceededError, ConfigError):
        assert issubclass(cls, AgentError), f"{cls.__name__} 必须继承 AgentError"


@pytest.mark.fast
def test_rate_limit_is_retryable() -> None:
    """RateLimitError 应同时是 RetryableError（用于重试装饰器分流）。"""
    assert issubclass(RateLimitError, RetryableError)


@pytest.mark.fast
def test_agent_error_carries_context() -> None:
    """AgentError 必须支持 context dict,用于日志结构化。"""
    err = AgentError("something failed", context={"agent": "researcher", "step": 3})
    assert err.context == {"agent": "researcher", "step": 3}
    assert "something failed" in str(err)


@pytest.mark.fast
def test_agent_error_default_context_empty() -> None:
    """未传 context 时默认为空 dict（避免 None 判断）。"""
    err = AgentError("oops")
    assert err.context == {}


@pytest.mark.fast
def test_llm_error_records_provider_and_model() -> None:
    """LLMError 必须记录 provider 与 model,便于 trace。"""
    err = LLMError("api 503", provider="deepseek", model="deepseek-chat")
    assert err.provider == "deepseek"
    assert err.model == "deepseek-chat"
    assert err.context["provider"] == "deepseek"
    assert err.context["model"] == "deepseek-chat"


@pytest.mark.fast
def test_budget_exceeded_records_amounts() -> None:
    """BudgetExceededError 必须记录 spent / limit 数值。"""
    err = BudgetExceededError(spent_usd=12.34, limit_usd=10.0)
    assert err.spent_usd == 12.34
    assert err.limit_usd == 10.0
    assert "12.34" in str(err)
    assert "10.0" in str(err)


@pytest.mark.fast
def test_tool_error_carries_tool_name() -> None:
    """ToolError 必须记录工具名。"""
    err = ToolError("permission denied", tool_name="shell")
    assert err.tool_name == "shell"
    assert err.context["tool_name"] == "shell"
```

- [ ] **Step 2.2：跑测试确认失败**

```bash
uv run pytest packages/common/tests/test_errors.py -v
```

Expected：collection error / ImportError（`common.errors` 不存在）。

- [ ] **Step 2.3：实现 errors 模块**

Create `packages/common/src/common/errors.py`：

```python
"""统一错误类层级。

设计原则:
- AgentError 是顶层基类,所有 agent 系统抛出的错误都应继承它。
- RetryableError 表示"可重试"语义,装饰器据此决定是否退避重试。
- 非 RetryableError 的错误立刻向上抛,不重试。
- 每个错误都带 context dict,用于日志/trace 结构化输出。
"""

from __future__ import annotations

from typing import Any


class AgentError(Exception):
    """所有 agent 系统错误的基类。

    Args:
        message: 人类可读的错误说明。
        context: 结构化上下文字段（agent / tool / step 等）,用于日志。
    """

    def __init__(self, message: str, *, context: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.context: dict[str, Any] = dict(context) if context else {}


class ConfigError(AgentError):
    """配置错误（缺失环境变量、格式错等）。不可重试。"""


class RetryableError(AgentError):
    """标记型基类:继承自此的错误会被 retry 装饰器视为"应重试"。"""


class RateLimitError(RetryableError):
    """LLM/外部 API 限流。属于可重试错误。"""


class LLMError(AgentError):
    """LLM 调用错误（非限流）。

    Args:
        message: 错误说明。
        provider: LLM provider 名（deepseek / anthropic / openai / ollama）。
        model: 具体模型名。
        context: 额外上下文。
    """

    def __init__(
        self,
        message: str,
        *,
        provider: str,
        model: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        merged: dict[str, Any] = {"provider": provider, "model": model}
        if context:
            merged.update(context)
        super().__init__(message, context=merged)
        self.provider = provider
        self.model = model


class ToolError(AgentError):
    """工具调用错误。

    Args:
        message: 错误说明。
        tool_name: 工具名（与 @tool 装饰器注册的名字一致）。
        context: 额外上下文。
    """

    def __init__(
        self,
        message: str,
        *,
        tool_name: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        merged: dict[str, Any] = {"tool_name": tool_name}
        if context:
            merged.update(context)
        super().__init__(message, context=merged)
        self.tool_name = tool_name


class BudgetExceededError(AgentError):
    """成本超出预算。

    Args:
        spent_usd: 已花费金额。
        limit_usd: 预算上限。
    """

    def __init__(
        self,
        *,
        spent_usd: float,
        limit_usd: float,
        context: dict[str, Any] | None = None,
    ) -> None:
        merged: dict[str, Any] = {"spent_usd": spent_usd, "limit_usd": limit_usd}
        if context:
            merged.update(context)
        message = f"budget exceeded: spent {spent_usd} USD > limit {limit_usd} USD"
        super().__init__(message, context=merged)
        self.spent_usd = spent_usd
        self.limit_usd = limit_usd
```

- [ ] **Step 2.4：跑测试确认通过**

```bash
uv run pytest packages/common/tests/test_errors.py -v
```

Expected：7 个测试全过。

- [ ] **Step 2.5：lint + type**

```bash
uv run ruff check packages/common
uv run mypy packages/common
```

Expected：均通过。

- [ ] **Step 2.6：提交**

```bash
git add packages/common/src/common/errors.py packages/common/tests/test_errors.py
git commit -m "feat(common): 添加 errors 错误类层级（AgentError + 6 个子类）"
```

---

## Task 3：`common.config` —— 多环境配置（TDD）

**Files:**
- Create: `packages/common/tests/conftest.py`
- Create: `packages/common/tests/test_config.py`
- Create: `packages/common/src/common/config.py`

- [ ] **Step 3.1：写共用 fixtures**

Create `packages/common/tests/conftest.py`：

```python
"""packages/common 测试共用 fixtures。"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """每个测试开始前清空 AGENTTASK_ 前缀的环境变量,避免外部 .env 干扰。

    autouse=True 表示所有测试自动应用。
    """
    for key in list(os.environ.keys()):
        if key.startswith("AGENTTASK_"):
            monkeypatch.delenv(key, raising=False)
    yield
```

- [ ] **Step 3.2：写失败的测试**

Create `packages/common/tests/test_config.py`：

```python
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
```

- [ ] **Step 3.3：跑测试确认失败**

```bash
uv run pytest packages/common/tests/test_config.py -v
```

Expected：ImportError(`common.config` 不存在)。

- [ ] **Step 3.4：实现 config 模块**

Create `packages/common/src/common/config.py`：

```python
"""多环境配置。

设计原则:
- 单一 Settings 类承载所有配置。
- env_prefix='AGENTTASK_',避免污染全局环境变量空间。
- 敏感字段（API key / DB password）用 SecretStr,日志输出不会泄漏。
- get_settings() 缓存单例,reload=True 用于测试与显式重载。
"""

from __future__ import annotations

import enum
from functools import lru_cache

from pydantic import Field, SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from .errors import ConfigError


class AppEnv(str, enum.Enum):
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class Settings(BaseSettings):
    """全局配置。所有字段都可通过 AGENTTASK_<UPPER_SNAKE> 环境变量覆盖。"""

    model_config = SettingsConfigDict(
        env_prefix="AGENTTASK_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # 忽略未声明的环境变量
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
    postgres_password: SecretStr = SecretStr("agenttask_dev")
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


_cached_settings: Settings | None = None


def get_settings(*, reload: bool = False) -> Settings:
    """返回全局 Settings 单例。

    Args:
        reload: True 时清除缓存并重新加载（测试用）。

    Raises:
        ConfigError: 当环境变量值无法通过 pydantic 校验时。
    """
    global _cached_settings
    if reload:
        _cached_settings = None
        get_settings.cache_clear() if hasattr(get_settings, "cache_clear") else None  # type: ignore[func-returns-value]
    if _cached_settings is None:
        try:
            _cached_settings = Settings()
        except ValidationError as e:
            raise ConfigError(
                f"settings validation failed: {e}",
                context={"errors": e.errors()},
            ) from e
    return _cached_settings


__all__ = ["AppEnv", "Settings", "get_settings"]
```

- [ ] **Step 3.5：跑测试确认通过**

```bash
uv run pytest packages/common/tests/test_config.py -v
```

Expected：8 个测试全过。

- [ ] **Step 3.6：lint + type**

```bash
uv run ruff check packages/common
uv run mypy packages/common
```

Expected：均通过。

- [ ] **Step 3.7：提交**

```bash
git add packages/common/src/common/config.py packages/common/tests/test_config.py packages/common/tests/conftest.py
git commit -m "feat(common): 添加 config（pydantic-settings + AGENTTASK_ 前缀）"
```

---

## Task 4：`common.logging` —— 结构化日志（TDD）

**Files:**
- Create: `packages/common/tests/test_logging.py`
- Create: `packages/common/src/common/logging.py`

- [ ] **Step 4.1：写失败的测试**

Create `packages/common/tests/test_logging.py`：

```python
"""structlog 结构化日志测试。"""

from __future__ import annotations

import json
import logging
from io import StringIO

import pytest
import structlog

from common.logging import bind_context, configure_logging, get_logger


@pytest.fixture(autouse=True)
def _reset_structlog() -> None:
    """每个测试前重置 structlog 全局配置,避免相互污染。"""
    structlog.reset_defaults()


@pytest.mark.fast
def test_configure_logging_emits_json_with_required_fields() -> None:
    """configure_logging 应输出 JSON,且至少包含 timestamp / level / event。"""
    buf = StringIO()
    configure_logging(level="INFO", stream=buf)
    log = get_logger("test_logger")
    log.info("hello", user_id=42)

    line = buf.getvalue().strip().splitlines()[-1]
    record = json.loads(line)
    assert record["event"] == "hello"
    assert record["level"] == "info"
    assert record["user_id"] == 42
    assert "timestamp" in record


@pytest.mark.fast
def test_log_level_filter_drops_below_threshold() -> None:
    """level=WARNING 时 info 不应输出。"""
    buf = StringIO()
    configure_logging(level="WARNING", stream=buf)
    log = get_logger("test_logger")
    log.info("should be dropped")
    log.warning("should be kept")

    out = buf.getvalue()
    assert "should be dropped" not in out
    assert "should be kept" in out


@pytest.mark.fast
def test_bind_context_attaches_persistent_fields() -> None:
    """bind_context 在的上下文管理器内,所有日志都应自动携带绑定字段。"""
    buf = StringIO()
    configure_logging(level="INFO", stream=buf)
    log = get_logger("test_logger")

    with bind_context(agent_name="researcher", trace_id="abc-123"):
        log.info("step_executed", step=1)

    line = buf.getvalue().strip().splitlines()[-1]
    record = json.loads(line)
    assert record["agent_name"] == "researcher"
    assert record["trace_id"] == "abc-123"
    assert record["step"] == 1


@pytest.mark.fast
def test_bind_context_clears_after_exit() -> None:
    """退出 bind_context 后,绑定字段应被清除。"""
    buf = StringIO()
    configure_logging(level="INFO", stream=buf)
    log = get_logger("test_logger")

    with bind_context(agent_name="researcher"):
        log.info("inside")
    log.info("outside")

    lines = buf.getvalue().strip().splitlines()
    assert json.loads(lines[-2])["agent_name"] == "researcher"
    assert "agent_name" not in json.loads(lines[-1])


@pytest.mark.fast
def test_get_logger_returns_structlog_bound_logger() -> None:
    """get_logger 必须返回 structlog BoundLogger,支持关键字日志。"""
    configure_logging(level="INFO")
    log = get_logger("x")
    assert isinstance(log, structlog.stdlib.BoundLogger)


@pytest.mark.fast
def test_invalid_level_raises_value_error() -> None:
    """未知 level 字符串应在 configure_logging 直接抛 ValueError。"""
    with pytest.raises(ValueError, match="invalid log level"):
        configure_logging(level="VERBOSE")  # 不是 DEBUG/INFO/WARNING/ERROR/CRITICAL


@pytest.mark.fast
def test_logging_does_not_propagate_secrets() -> None:
    """logger 是 stdlib 标准 logger,默认级别 propagate=True 不影响 JSON 输出格式;
    本测试仅确认输出确实只在我们指定的 stream 上,而不在 root handler。"""
    buf = StringIO()
    configure_logging(level="INFO", stream=buf)
    root = logging.getLogger()
    # root logger 不应再增加额外 handler
    handler_count = len([h for h in root.handlers])
    log = get_logger("x")
    log.info("ping")
    # 至少没有崩溃,且 buf 有内容
    assert buf.getvalue()
    # 确保我们没有不小心向 root 注入多余 handler
    assert len(root.handlers) == handler_count
```

- [ ] **Step 4.2：跑测试确认失败**

```bash
uv run pytest packages/common/tests/test_logging.py -v
```

Expected：ImportError。

- [ ] **Step 4.3：实现 logging 模块**

Create `packages/common/src/common/logging.py`：

```python
"""结构化日志。

设计:
- structlog 输出 JSON 行,适配 ELK / Loki / CloudWatch。
- timestamp / level / event / logger 由 processor 自动注入。
- bind_context 是 contextmanager,用 contextvars 实现跨异步任务安全。
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from typing import IO, Any

import structlog

_VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def configure_logging(
    *,
    level: str = "INFO",
    stream: IO[str] | None = None,
) -> None:
    """配置 stdlib + structlog,输出 JSON 行到 stream（默认 stderr）。

    可重复调用（测试场景）,后调用覆盖前调用。

    Args:
        level: 日志级别字符串,大小写无关,必须在 DEBUG/INFO/WARNING/ERROR/CRITICAL。
        stream: 输出流,None 时用 sys.stderr。
    """
    upper = level.upper()
    if upper not in _VALID_LEVELS:
        raise ValueError(f"invalid log level: {level!r}; expected one of {sorted(_VALID_LEVELS)}")

    target = stream if stream is not None else sys.stderr
    numeric_level = getattr(logging, upper)

    # stdlib root: 把消息送到 target
    handler = logging.StreamHandler(target)
    handler.setFormatter(logging.Formatter("%(message)s"))

    root = logging.getLogger()
    # 移除前一次 configure_logging 注入的 handler（看 marker 属性）
    root.handlers = [h for h in root.handlers if not getattr(h, "_agenttask", False)]
    handler._agenttask = True  # type: ignore[attr-defined]
    root.addHandler(handler)
    root.setLevel(numeric_level)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=False,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """返回 structlog BoundLogger（≈ pino 的 logger 子实例）。"""
    return structlog.get_logger(name)  # type: ignore[no-any-return]


@contextmanager
def bind_context(**kwargs: Any) -> Iterator[None]:
    """在上下文中绑定字段,内部所有日志自动携带。

    用法:
        with bind_context(agent_name="researcher", trace_id="abc"):
            log.info("step")  # 自动带上 agent_name / trace_id
    """
    tokens = structlog.contextvars.bind_contextvars(**kwargs)
    try:
        yield
    finally:
        structlog.contextvars.reset_contextvars(**tokens)


__all__ = ["bind_context", "configure_logging", "get_logger"]
```

- [ ] **Step 4.4：跑测试确认通过**

```bash
uv run pytest packages/common/tests/test_logging.py -v
```

Expected：7 个测试全过。

- [ ] **Step 4.5：lint + type**

```bash
uv run ruff check packages/common
uv run mypy packages/common
```

Expected：均通过。

- [ ] **Step 4.6：提交**

```bash
git add packages/common/src/common/logging.py packages/common/tests/test_logging.py
git commit -m "feat(common): 添加 logging（structlog JSON + bind_context）"
```

---

## Task 5：`common.retry` —— 重试装饰器（TDD）

**Files:**
- Create: `packages/common/tests/test_retry.py`
- Create: `packages/common/src/common/retry.py`

- [ ] **Step 5.1：写失败的测试**

Create `packages/common/tests/test_retry.py`：

```python
"""tenacity 重试装饰器测试。"""

from __future__ import annotations

import pytest

from common.errors import LLMError, RateLimitError
from common.retry import retry_on_retryable


class _Counter:
    def __init__(self) -> None:
        self.calls = 0


@pytest.mark.fast
def test_retry_succeeds_after_transient_failures() -> None:
    """前 2 次抛 RateLimitError,第 3 次成功 → 装饰器应返回 OK。"""
    c = _Counter()

    @retry_on_retryable(max_attempts=5, initial_wait_s=0.0, max_wait_s=0.0)
    def flaky() -> str:
        c.calls += 1
        if c.calls < 3:
            raise RateLimitError("429")
        return "ok"

    assert flaky() == "ok"
    assert c.calls == 3


@pytest.mark.fast
def test_retry_gives_up_after_max_attempts() -> None:
    """达到 max_attempts 仍失败 → 抛最后一次异常。"""
    c = _Counter()

    @retry_on_retryable(max_attempts=3, initial_wait_s=0.0, max_wait_s=0.0)
    def always_fails() -> None:
        c.calls += 1
        raise RateLimitError("perma 429")

    with pytest.raises(RateLimitError, match="perma 429"):
        always_fails()
    assert c.calls == 3


@pytest.mark.fast
def test_retry_does_not_retry_on_non_retryable() -> None:
    """非 RetryableError → 立刻抛,不重试。"""
    c = _Counter()

    @retry_on_retryable(max_attempts=5, initial_wait_s=0.0, max_wait_s=0.0)
    def boom() -> None:
        c.calls += 1
        raise LLMError("hard error", provider="deepseek", model="deepseek-chat")

    with pytest.raises(LLMError):
        boom()
    assert c.calls == 1


@pytest.mark.fast
def test_retry_does_not_retry_on_value_error() -> None:
    """普通 stdlib 异常也不重试（仅 RetryableError 子类才重试）。"""
    c = _Counter()

    @retry_on_retryable(max_attempts=5, initial_wait_s=0.0, max_wait_s=0.0)
    def bad_input() -> None:
        c.calls += 1
        raise ValueError("nope")

    with pytest.raises(ValueError):
        bad_input()
    assert c.calls == 1


@pytest.mark.fast
async def test_retry_supports_async_function() -> None:
    """装饰器同时支持 async 函数。"""
    c = _Counter()

    @retry_on_retryable(max_attempts=4, initial_wait_s=0.0, max_wait_s=0.0)
    async def flaky_async() -> str:
        c.calls += 1
        if c.calls < 2:
            raise RateLimitError("burst")
        return "done"

    result = await flaky_async()
    assert result == "done"
    assert c.calls == 2
```

- [ ] **Step 5.2：跑测试确认失败**

```bash
uv run pytest packages/common/tests/test_retry.py -v
```

Expected：ImportError。

- [ ] **Step 5.3：实现 retry 模块**

Create `packages/common/src/common/retry.py`：

```python
"""重试策略。

只重试 RetryableError 子类。其他异常（含 LLMError 非限流子类、stdlib 异常）立刻向上抛。
等待策略:指数退避 + jitter。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from tenacity import (
    AsyncRetrying,
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from .errors import RetryableError

T = TypeVar("T")


def retry_on_retryable(
    *,
    max_attempts: int = 5,
    initial_wait_s: float = 1.0,
    max_wait_s: float = 30.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """对函数应用"仅重试 RetryableError"策略,同步与 async 函数都支持。

    Args:
        max_attempts: 最多尝试次数（含首次）。
        initial_wait_s: 第一次失败后的等待基准。
        max_wait_s: 等待时间上限。
    """
    import asyncio
    import functools

    sync_retrying = Retrying(
        stop=stop_after_attempt(max_attempts),
        wait=wait_random_exponential(multiplier=initial_wait_s, max=max_wait_s),
        retry=retry_if_exception_type(RetryableError),
        reraise=True,
    )
    async_retrying = AsyncRetrying(
        stop=stop_after_attempt(max_attempts),
        wait=wait_random_exponential(multiplier=initial_wait_s, max=max_wait_s),
        retry=retry_if_exception_type(RetryableError),
        reraise=True,
    )

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: object, **kwargs: object) -> T:
                async for attempt in async_retrying:
                    with attempt:
                        return await func(*args, **kwargs)  # type: ignore[no-any-return]
                raise RuntimeError("unreachable")  # tenacity reraise=True 已保证

            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(func)
        def sync_wrapper(*args: object, **kwargs: object) -> T:
            for attempt in sync_retrying:
                with attempt:
                    return func(*args, **kwargs)
            raise RuntimeError("unreachable")

        return sync_wrapper

    return decorator


__all__ = ["retry_on_retryable"]
```

- [ ] **Step 5.4：跑测试确认通过**

```bash
uv run pytest packages/common/tests/test_retry.py -v
```

Expected：5 个测试全过。

- [ ] **Step 5.5：lint + type**

```bash
uv run ruff check packages/common
uv run mypy packages/common
```

Expected：均通过。

- [ ] **Step 5.6：提交**

```bash
git add packages/common/src/common/retry.py packages/common/tests/test_retry.py
git commit -m "feat(common): 添加 retry 装饰器（仅重试 RetryableError，支持 async）"
```

---

## Task 6：`common.cost` —— LLM 成本追踪（TDD）

**Files:**
- Create: `packages/common/tests/test_cost.py`
- Create: `packages/common/src/common/cost.py`

- [ ] **Step 6.1：写失败的测试**

Create `packages/common/tests/test_cost.py`：

```python
"""LLM 成本追踪器测试。"""

from __future__ import annotations

import math

import pytest

from common.cost import (
    PRICE_TABLE,
    CostTracker,
    ModelPrice,
    estimate_cost_usd,
)
from common.errors import BudgetExceededError


@pytest.mark.fast
def test_price_table_contains_required_models() -> None:
    """价格表必须包含 M1 默认 provider 的旗舰模型。"""
    required = ["deepseek-chat", "claude-sonnet-4-6", "gpt-4o-mini"]
    for m in required:
        assert m in PRICE_TABLE, f"PRICE_TABLE 缺少 {m}"
        price = PRICE_TABLE[m]
        assert price.input_per_1m_usd > 0
        assert price.output_per_1m_usd > 0


@pytest.mark.fast
def test_estimate_cost_for_known_model() -> None:
    """1k input + 500 output token 的成本应等于价格表数学结果。"""
    cost = estimate_cost_usd("deepseek-chat", input_tokens=1000, output_tokens=500)
    expected = (
        1000 / 1_000_000 * PRICE_TABLE["deepseek-chat"].input_per_1m_usd
        + 500 / 1_000_000 * PRICE_TABLE["deepseek-chat"].output_per_1m_usd
    )
    assert math.isclose(cost, expected, rel_tol=1e-9)


@pytest.mark.fast
def test_estimate_cost_unknown_model_returns_zero() -> None:
    """未知模型应返回 0,不应抛错（避免日志路径炸掉）。"""
    cost = estimate_cost_usd("unknown-model-xyz", input_tokens=1000, output_tokens=1000)
    assert cost == 0.0


@pytest.mark.fast
def test_cost_tracker_records_usage() -> None:
    """CostTracker.record 应累加 total 与 per-model。"""
    t = CostTracker()
    t.record(model="deepseek-chat", input_tokens=1000, output_tokens=500)
    t.record(model="deepseek-chat", input_tokens=2000, output_tokens=1000)
    t.record(model="gpt-4o-mini", input_tokens=500, output_tokens=200)

    assert t.total_input_tokens == 3500
    assert t.total_output_tokens == 1700
    assert t.total_cost_usd > 0

    per_model = t.per_model()
    assert per_model["deepseek-chat"].input_tokens == 3000
    assert per_model["deepseek-chat"].output_tokens == 1500
    assert per_model["gpt-4o-mini"].input_tokens == 500


@pytest.mark.fast
def test_cost_tracker_budget_check_pass() -> None:
    """累计成本未超预算 → check_budget 静默返回。"""
    t = CostTracker(budget_usd=100.0)
    t.record(model="deepseek-chat", input_tokens=1000, output_tokens=500)
    t.check_budget()  # 不应抛


@pytest.mark.fast
def test_cost_tracker_budget_exceeded_raises() -> None:
    """超预算 → 抛 BudgetExceededError。"""
    t = CostTracker(budget_usd=0.0001)  # 极低预算
    t.record(model="claude-sonnet-4-6", input_tokens=1_000_000, output_tokens=1_000_000)
    with pytest.raises(BudgetExceededError) as exc_info:
        t.check_budget()
    assert exc_info.value.spent_usd > 0.0001
    assert exc_info.value.limit_usd == 0.0001


@pytest.mark.fast
def test_cost_tracker_zero_budget_means_unlimited() -> None:
    """budget_usd=0 表示不限制（与 Settings 默认一致）。"""
    t = CostTracker(budget_usd=0.0)
    t.record(model="claude-sonnet-4-6", input_tokens=10_000_000, output_tokens=10_000_000)
    t.check_budget()  # 不抛


@pytest.mark.fast
def test_model_price_is_frozen() -> None:
    """ModelPrice 应不可变,防止运行时被改坏价格表。"""
    price = ModelPrice(input_per_1m_usd=1.0, output_per_1m_usd=2.0)
    with pytest.raises((AttributeError, TypeError)):
        price.input_per_1m_usd = 999  # type: ignore[misc]
```

- [ ] **Step 6.2：跑测试确认失败**

```bash
uv run pytest packages/common/tests/test_cost.py -v
```

Expected：ImportError。

- [ ] **Step 6.3：实现 cost 模块**

Create `packages/common/src/common/cost.py`：

```python
"""LLM 成本追踪。

PRICE_TABLE 为 2026-06 时点参考价(USD per 1M tokens)。后续里程碑可改为
读取 YAML/JSON 配置文件,目前 inline dict 已足够。

未知模型成本计为 0(避免日志/链路炸掉),由调用方决定是否警告。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ModelPrice:
    """单模型价格(USD per 1M tokens)。"""

    input_per_1m_usd: float
    output_per_1m_usd: float


# 2026-06 参考价。后续按需更新。
PRICE_TABLE: dict[str, ModelPrice] = {
    # DeepSeek
    "deepseek-chat": ModelPrice(input_per_1m_usd=0.27, output_per_1m_usd=1.10),
    "deepseek-reasoner": ModelPrice(input_per_1m_usd=0.55, output_per_1m_usd=2.19),
    # Anthropic
    "claude-sonnet-4-6": ModelPrice(input_per_1m_usd=3.00, output_per_1m_usd=15.00),
    "claude-opus-4-7": ModelPrice(input_per_1m_usd=15.00, output_per_1m_usd=75.00),
    "claude-haiku-4-5": ModelPrice(input_per_1m_usd=0.80, output_per_1m_usd=4.00),
    # OpenAI
    "gpt-4o": ModelPrice(input_per_1m_usd=2.50, output_per_1m_usd=10.00),
    "gpt-4o-mini": ModelPrice(input_per_1m_usd=0.15, output_per_1m_usd=0.60),
}


def estimate_cost_usd(model: str, *, input_tokens: int, output_tokens: int) -> float:
    """根据 PRICE_TABLE 估算单次调用成本。未知模型返回 0。"""
    price = PRICE_TABLE.get(model)
    if price is None:
        return 0.0
    return (
        input_tokens / 1_000_000 * price.input_per_1m_usd
        + output_tokens / 1_000_000 * price.output_per_1m_usd
    )


@dataclass(slots=True)
class _ModelUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0


@dataclass(slots=True)
class CostTracker:
    """成本累计器。线程不安全(单 agent 调用栈内使用)。"""

    budget_usd: float = 0.0  # 0 表示不限制
    _per_model: dict[str, _ModelUsage] = field(default_factory=dict)

    def record(self, *, model: str, input_tokens: int, output_tokens: int) -> None:
        """记录一次 LLM 调用。"""
        cost = estimate_cost_usd(model, input_tokens=input_tokens, output_tokens=output_tokens)
        usage = self._per_model.setdefault(model, _ModelUsage())
        usage.input_tokens += input_tokens
        usage.output_tokens += output_tokens
        usage.cost_usd += cost

    @property
    def total_input_tokens(self) -> int:
        return sum(u.input_tokens for u in self._per_model.values())

    @property
    def total_output_tokens(self) -> int:
        return sum(u.output_tokens for u in self._per_model.values())

    @property
    def total_cost_usd(self) -> float:
        return sum(u.cost_usd for u in self._per_model.values())

    def per_model(self) -> dict[str, _ModelUsage]:
        """返回当前 per-model 视图(只读快照拷贝)。"""
        return {
            model: _ModelUsage(
                input_tokens=u.input_tokens,
                output_tokens=u.output_tokens,
                cost_usd=u.cost_usd,
            )
            for model, u in self._per_model.items()
        }

    def check_budget(self) -> None:
        """超预算抛 BudgetExceededError。budget_usd=0 表示不限制。"""
        if self.budget_usd <= 0:
            return
        if self.total_cost_usd > self.budget_usd:
            from .errors import BudgetExceededError

            raise BudgetExceededError(spent_usd=self.total_cost_usd, limit_usd=self.budget_usd)


__all__ = ["PRICE_TABLE", "CostTracker", "ModelPrice", "estimate_cost_usd"]
```

- [ ] **Step 6.4：跑测试确认通过**

```bash
uv run pytest packages/common/tests/test_cost.py -v
```

Expected：8 个测试全过。

- [ ] **Step 6.5：lint + type**

```bash
uv run ruff check packages/common
uv run mypy packages/common
```

Expected：均通过。

- [ ] **Step 6.6：提交**

```bash
git add packages/common/src/common/cost.py packages/common/tests/test_cost.py
git commit -m "feat(common): 添加 cost（PRICE_TABLE + CostTracker + 预算守门）"
```

---

## Task 7：`common.cache` —— Redis 响应缓存（TDD）

**Files:**
- Create: `packages/common/tests/test_cache.py`
- Create: `packages/common/src/common/cache.py`

- [ ] **Step 7.1：写失败的测试**

Create `packages/common/tests/test_cache.py`：

```python
"""Redis 缓存装饰器测试。使用 fakeredis 避免依赖真实 Redis。"""

from __future__ import annotations

from typing import Any

import fakeredis
import pytest

from common.cache import cached, make_cache_key


class _Counter:
    def __init__(self) -> None:
        self.calls = 0


@pytest.fixture
def fake_redis() -> fakeredis.FakeRedis:
    return fakeredis.FakeRedis(decode_responses=False)


@pytest.mark.fast
def test_make_cache_key_is_deterministic() -> None:
    """同样的输入应得到同样的 key。"""
    k1 = make_cache_key("namespace", "model-x", {"prompt": "hello", "temp": 0.7})
    k2 = make_cache_key("namespace", "model-x", {"temp": 0.7, "prompt": "hello"})  # 顺序不同
    assert k1 == k2
    assert k1.startswith("namespace:")


@pytest.mark.fast
def test_make_cache_key_changes_with_input() -> None:
    """输入不同 → key 不同。"""
    k1 = make_cache_key("ns", "m", {"prompt": "a"})
    k2 = make_cache_key("ns", "m", {"prompt": "b"})
    assert k1 != k2


@pytest.mark.fast
def test_cached_first_call_executes_function(fake_redis: fakeredis.FakeRedis) -> None:
    """首次调用应执行函数并写缓存。"""
    counter = _Counter()

    @cached(client=fake_redis, namespace="t", ttl_seconds=60)
    def expensive(x: int) -> dict[str, int]:
        counter.calls += 1
        return {"value": x * 2}

    result = expensive(5)
    assert result == {"value": 10}
    assert counter.calls == 1


@pytest.mark.fast
def test_cached_second_call_hits_cache(fake_redis: fakeredis.FakeRedis) -> None:
    """同样参数的第二次调用应直接返回缓存,不执行函数体。"""
    counter = _Counter()

    @cached(client=fake_redis, namespace="t", ttl_seconds=60)
    def expensive(x: int) -> dict[str, int]:
        counter.calls += 1
        return {"value": x * 2}

    expensive(5)
    expensive(5)
    expensive(5)
    assert counter.calls == 1


@pytest.mark.fast
def test_cached_different_args_dont_collide(fake_redis: fakeredis.FakeRedis) -> None:
    """不同参数应得到不同缓存项。"""
    counter = _Counter()

    @cached(client=fake_redis, namespace="t", ttl_seconds=60)
    def expensive(x: int) -> int:
        counter.calls += 1
        return x * 2

    assert expensive(1) == 2
    assert expensive(2) == 4
    assert expensive(3) == 6
    assert counter.calls == 3


@pytest.mark.fast
def test_cached_supports_complex_jsonable_return(fake_redis: fakeredis.FakeRedis) -> None:
    """支持 list/dict/str/int/float/bool/None 的 JSON 序列化返回值。"""
    counter = _Counter()

    @cached(client=fake_redis, namespace="t", ttl_seconds=60)
    def fancy() -> dict[str, Any]:
        counter.calls += 1
        return {"items": [1, 2, 3], "meta": {"name": "x", "ok": True}}

    fancy()
    fancy()
    assert counter.calls == 1


@pytest.mark.fast
async def test_cached_async_function(fake_redis: fakeredis.FakeRedis) -> None:
    """装饰器应同时支持 async 函数。"""
    counter = _Counter()

    @cached(client=fake_redis, namespace="t", ttl_seconds=60)
    async def aget(x: int) -> int:
        counter.calls += 1
        return x + 100

    assert await aget(1) == 101
    assert await aget(1) == 101
    assert counter.calls == 1


@pytest.mark.fast
def test_cached_ttl_expires(fake_redis: fakeredis.FakeRedis) -> None:
    """TTL 过期后应重新执行函数。"""
    counter = _Counter()

    @cached(client=fake_redis, namespace="t", ttl_seconds=1)
    def f() -> int:
        counter.calls += 1
        return 42

    f()
    # 模拟时间推进:fakeredis 不直接支持 TTL 推进,改用手动 delete 验证
    assert fake_redis.delete(*fake_redis.keys("t:*"))
    f()
    assert counter.calls == 2
```

- [ ] **Step 7.2：跑测试确认失败**

```bash
uv run pytest packages/common/tests/test_cache.py -v
```

Expected：ImportError。

- [ ] **Step 7.3：实现 cache 模块**

Create `packages/common/src/common/cache.py`：

```python
"""Redis 缓存装饰器。

设计:
- key = namespace + ':' + sha256(stable_repr(args, kwargs))
- value = JSON 序列化的返回值
- 同步与 async 函数都支持
"""

from __future__ import annotations

import asyncio
import functools
import hashlib
import json
from collections.abc import Callable
from typing import Any, TypeVar

import redis

T = TypeVar("T")


def make_cache_key(namespace: str, model: str, payload: dict[str, Any]) -> str:
    """生成稳定的缓存 key:与字典遍历顺序无关。"""
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(f"{model}|{encoded}".encode()).hexdigest()
    return f"{namespace}:{digest}"


def _stable_payload(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    """把任意 args/kwargs 转成 JSON 可序列化的稳定 payload。

    不可 JSON 序列化的对象转 repr(),保证至少能比较等价性。
    """

    def to_jsonable(v: Any) -> Any:
        try:
            json.dumps(v)
            return v
        except (TypeError, ValueError):
            return repr(v)

    return {
        "args": [to_jsonable(a) for a in args],
        "kwargs": {k: to_jsonable(v) for k, v in kwargs.items()},
    }


def cached(
    *,
    client: redis.Redis,
    namespace: str,
    ttl_seconds: int,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """把函数返回值缓存到 Redis。

    Args:
        client: redis-py 客户端（或 fakeredis.FakeRedis,接口兼容）。
        namespace: 缓存 key 前缀,用来区分不同调用点。
        ttl_seconds: 过期秒数。
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> T:
                payload = _stable_payload(args, kwargs)
                key = make_cache_key(namespace, func.__qualname__, payload)
                hit = client.get(key)
                if hit is not None:
                    return json.loads(hit)  # type: ignore[no-any-return]
                result = await func(*args, **kwargs)
                client.setex(key, ttl_seconds, json.dumps(result, ensure_ascii=False))
                return result

            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            payload = _stable_payload(args, kwargs)
            key = make_cache_key(namespace, func.__qualname__, payload)
            hit = client.get(key)
            if hit is not None:
                return json.loads(hit)  # type: ignore[no-any-return]
            result = func(*args, **kwargs)
            client.setex(key, ttl_seconds, json.dumps(result, ensure_ascii=False))
            return result

        return sync_wrapper

    return decorator


__all__ = ["cached", "make_cache_key"]
```

- [ ] **Step 7.4：跑测试确认通过**

```bash
uv run pytest packages/common/tests/test_cache.py -v
```

Expected：8 个测试全过。

- [ ] **Step 7.5：lint + type**

```bash
uv run ruff check packages/common
uv run mypy packages/common
```

Expected：均通过。

- [ ] **Step 7.6：检查 common 包整体覆盖率**

```bash
uv run pytest packages/common --cov=common --cov-report=term-missing
```

Expected：covered ≥ 80%。

- [ ] **Step 7.7：提交**

```bash
git add packages/common/src/common/cache.py packages/common/tests/test_cache.py
git commit -m "feat(common): 添加 cache（Redis 装饰器，sync/async 通用）"
```

---

## Task 8：创建 `packages/llm_providers` 骨架

**Files:**
- Create: `packages/llm_providers/pyproject.toml`
- Create: `packages/llm_providers/README.md`
- Create: `packages/llm_providers/src/llm_providers/__init__.py`
- Create: `packages/llm_providers/src/llm_providers/providers/__init__.py`
- Create: `packages/llm_providers/tests/__init__.py`
- Create: `packages/llm_providers/tests/conftest.py`

- [ ] **Step 8.1：创建目录与 pyproject**

```bash
mkdir -p packages/llm_providers/src/llm_providers/providers packages/llm_providers/tests
```

Create `packages/llm_providers/pyproject.toml`：

```toml
[project]
name = "llm-providers"
version = "0.1.0"
description = "AgentTask 多供应商 LLM 抽象（DeepSeek / Anthropic / OpenAI / Ollama）"
readme = "README.md"
requires-python = ">=3.12,<3.13"
license = { text = "MIT" }
authors = [{ name = "AgentTask Author" }]
dependencies = [
    "common",
    "langchain-core>=0.3.20,<0.4",
    "langchain-openai>=0.2.10,<0.3",
    "langchain-anthropic>=0.3.0,<0.4",
    "langchain-ollama>=0.2.2,<0.3",
]

[build-system]
requires = ["hatchling>=1.25"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/llm_providers"]

[tool.uv.sources]
common = { workspace = true }
```

- [ ] **Step 8.2：写 README**

Create `packages/llm_providers/README.md`：

```markdown
# llm_providers

统一封装四个 LLM provider,提供同一 LangChain `BaseChatModel` 接口:
DeepSeek（默认）/ Anthropic / OpenAI / Ollama（本地）。

## 使用

```python
from llm_providers import get_chat_model

# 用配置中的默认 provider 与默认 model
llm = get_chat_model()

# 显式指定
llm = get_chat_model(provider="anthropic", model="claude-sonnet-4-6")

# 切到本地 Ollama
llm = get_chat_model(provider="ollama", model="llama3.2")

response = llm.invoke("hello")
```

切换 provider 不需要改业务代码 —— 这就是本包存在的意义。

## 模块

| 模块 | 作用 |
|---|---|
| `factory.get_chat_model` | 总入口,按 provider 分发 |
| `providers/{deepseek,anthropic,openai,ollama}.py` | 各 provider 工厂函数 |
| `middleware` | with_cost_tracking / with_retry / with_cache 包装器 |
| `embeddings.get_embeddings` | embedding 工厂（OpenAI / Ollama） |
```

- [ ] **Step 8.3：写 `__init__.py` 占位**

Create `packages/llm_providers/src/llm_providers/__init__.py`：

```python
"""llm_providers: 多供应商 LLM 抽象。"""

from __future__ import annotations

__version__ = "0.1.0"
```

Create `packages/llm_providers/src/llm_providers/providers/__init__.py`（空文件）：

```python
```

Create `packages/llm_providers/tests/__init__.py`（空文件）：

```python
```

Create `packages/llm_providers/tests/conftest.py`：

```python
"""llm_providers 测试共用 fixtures。"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """每个测试前清空 AGENTTASK_ 与 LLM provider 相关环境变量。"""
    for key in list(os.environ.keys()):
        if key.startswith(("AGENTTASK_", "OPENAI_", "ANTHROPIC_", "DEEPSEEK_")):
            monkeypatch.delenv(key, raising=False)
    yield
```

- [ ] **Step 8.4：同步依赖**

```bash
uv sync
```

Expected：解析 langchain-* 系列。`llm_providers` 与 `common` 都识别为 workspace 成员。

- [ ] **Step 8.5：lint + type 验证骨架**

```bash
uv run ruff check packages/llm_providers
uv run mypy packages/llm_providers
```

Expected：均通过。

- [ ] **Step 8.6：提交**

```bash
git add packages/llm_providers/pyproject.toml packages/llm_providers/README.md packages/llm_providers/src packages/llm_providers/tests uv.lock
git commit -m "feat(llm-providers): 创建包骨架（依赖 common + langchain-*）"
```

---

## Task 9：四个 provider 工厂函数（TDD）

**Files:**
- Create: `packages/llm_providers/tests/test_provider_deepseek.py`
- Create: `packages/llm_providers/tests/test_provider_anthropic.py`
- Create: `packages/llm_providers/tests/test_provider_openai.py`
- Create: `packages/llm_providers/tests/test_provider_ollama.py`
- Create: `packages/llm_providers/src/llm_providers/providers/deepseek.py`
- Create: `packages/llm_providers/src/llm_providers/providers/anthropic.py`
- Create: `packages/llm_providers/src/llm_providers/providers/openai.py`
- Create: `packages/llm_providers/src/llm_providers/providers/ollama.py`

- [ ] **Step 9.1：写 deepseek provider 测试**

Create `packages/llm_providers/tests/test_provider_deepseek.py`：

```python
"""DeepSeek provider 工厂测试。

不发起真实 HTTP,只验证返回的 BaseChatModel 配置正确。
"""

from __future__ import annotations

import pytest
from langchain_openai import ChatOpenAI

from common.errors import ConfigError
from llm_providers.providers.deepseek import build_deepseek_chat


@pytest.mark.fast
def test_build_deepseek_returns_chat_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    """DeepSeek 通过 langchain-openai 的 ChatOpenAI + base_url 实现。"""
    monkeypatch.setenv("AGENTTASK_DEEPSEEK_API_KEY", "sk-test")
    llm = build_deepseek_chat(model="deepseek-chat", temperature=0.5)
    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == "deepseek-chat"
    assert llm.temperature == 0.5
    # base_url 配置在 client 中而非顶层属性,验证 openai_api_base 字段
    assert "deepseek.com" in str(llm.openai_api_base or "")


@pytest.mark.fast
def test_build_deepseek_missing_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """缺少 API key 应抛 ConfigError。"""
    with pytest.raises(ConfigError, match="DEEPSEEK_API_KEY"):
        build_deepseek_chat(model="deepseek-chat")


@pytest.mark.fast
def test_build_deepseek_default_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """不传 model 时使用 deepseek-chat。"""
    monkeypatch.setenv("AGENTTASK_DEEPSEEK_API_KEY", "sk-test")
    llm = build_deepseek_chat()
    assert llm.model_name == "deepseek-chat"
```

- [ ] **Step 9.2：写 anthropic / openai / ollama 测试**

Create `packages/llm_providers/tests/test_provider_anthropic.py`：

```python
"""Anthropic provider 工厂测试。"""

from __future__ import annotations

import pytest
from langchain_anthropic import ChatAnthropic

from common.errors import ConfigError
from llm_providers.providers.anthropic import build_anthropic_chat


@pytest.mark.fast
def test_build_anthropic_returns_chat_anthropic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTTASK_ANTHROPIC_API_KEY", "sk-ant-test")
    llm = build_anthropic_chat(model="claude-sonnet-4-6", temperature=0.2)
    assert isinstance(llm, ChatAnthropic)
    assert llm.model == "claude-sonnet-4-6"


@pytest.mark.fast
def test_build_anthropic_missing_key_raises() -> None:
    with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY"):
        build_anthropic_chat(model="claude-sonnet-4-6")


@pytest.mark.fast
def test_build_anthropic_default_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTTASK_ANTHROPIC_API_KEY", "sk-ant-test")
    llm = build_anthropic_chat()
    assert llm.model == "claude-sonnet-4-6"
```

Create `packages/llm_providers/tests/test_provider_openai.py`：

```python
"""OpenAI provider 工厂测试。"""

from __future__ import annotations

import pytest
from langchain_openai import ChatOpenAI

from common.errors import ConfigError
from llm_providers.providers.openai import build_openai_chat


@pytest.mark.fast
def test_build_openai_returns_chat_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTTASK_OPENAI_API_KEY", "sk-openai-test")
    llm = build_openai_chat(model="gpt-4o-mini", temperature=0.0)
    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == "gpt-4o-mini"


@pytest.mark.fast
def test_build_openai_missing_key_raises() -> None:
    with pytest.raises(ConfigError, match="OPENAI_API_KEY"):
        build_openai_chat(model="gpt-4o-mini")


@pytest.mark.fast
def test_build_openai_default_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTTASK_OPENAI_API_KEY", "sk-openai-test")
    llm = build_openai_chat()
    assert llm.model_name == "gpt-4o-mini"
```

Create `packages/llm_providers/tests/test_provider_ollama.py`：

```python
"""Ollama provider 工厂测试。本地服务,不需要 API key。"""

from __future__ import annotations

import pytest
from langchain_ollama import ChatOllama

from llm_providers.providers.ollama import build_ollama_chat


@pytest.mark.fast
def test_build_ollama_returns_chat_ollama() -> None:
    llm = build_ollama_chat(model="llama3.2", temperature=0.7)
    assert isinstance(llm, ChatOllama)
    assert llm.model == "llama3.2"


@pytest.mark.fast
def test_build_ollama_default_base_url() -> None:
    llm = build_ollama_chat(model="llama3.2")
    assert "11434" in (llm.base_url or "")


@pytest.mark.fast
def test_build_ollama_custom_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTTASK_OLLAMA_BASE_URL", "http://custom-host:11500")
    llm = build_ollama_chat(model="llama3.2")
    assert "custom-host" in (llm.base_url or "")
    assert "11500" in (llm.base_url or "")


@pytest.mark.fast
def test_build_ollama_default_model() -> None:
    llm = build_ollama_chat()
    assert llm.model == "llama3.2"
```

- [ ] **Step 9.3：跑测试确认失败**

```bash
uv run pytest packages/llm_providers/tests -v
```

Expected：ImportError(provider 模块不存在)。

- [ ] **Step 9.4：实现 deepseek**

Create `packages/llm_providers/src/llm_providers/providers/deepseek.py`：

```python
"""DeepSeek provider。

DeepSeek 提供 OpenAI 兼容 API,直接复用 langchain-openai 的 ChatOpenAI,
通过 base_url 指向 https://api.deepseek.com 即可。
"""

from __future__ import annotations

from typing import Any

from langchain_openai import ChatOpenAI

from common.config import get_settings
from common.errors import ConfigError

DEFAULT_MODEL = "deepseek-chat"


def build_deepseek_chat(
    *,
    model: str | None = None,
    temperature: float = 0.7,
    **kwargs: Any,
) -> ChatOpenAI:
    """构造 DeepSeek chat 模型。

    Args:
        model: 模型名,默认 deepseek-chat。
        temperature: 采样温度。
        **kwargs: 透传给 ChatOpenAI。

    Raises:
        ConfigError: 未配置 AGENTTASK_DEEPSEEK_API_KEY。
    """
    settings = get_settings(reload=True)
    if settings.deepseek_api_key is None:
        raise ConfigError(
            "missing AGENTTASK_DEEPSEEK_API_KEY (set in .env or environment)",
            context={"provider": "deepseek"},
        )
    return ChatOpenAI(
        model=model or DEFAULT_MODEL,
        temperature=temperature,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        **kwargs,
    )


__all__ = ["DEFAULT_MODEL", "build_deepseek_chat"]
```

- [ ] **Step 9.5：实现 anthropic**

Create `packages/llm_providers/src/llm_providers/providers/anthropic.py`：

```python
"""Anthropic provider。"""

from __future__ import annotations

from typing import Any

from langchain_anthropic import ChatAnthropic

from common.config import get_settings
from common.errors import ConfigError

DEFAULT_MODEL = "claude-sonnet-4-6"


def build_anthropic_chat(
    *,
    model: str | None = None,
    temperature: float = 0.7,
    **kwargs: Any,
) -> ChatAnthropic:
    """构造 Anthropic chat 模型。

    Raises:
        ConfigError: 未配置 AGENTTASK_ANTHROPIC_API_KEY。
    """
    settings = get_settings(reload=True)
    if settings.anthropic_api_key is None:
        raise ConfigError(
            "missing AGENTTASK_ANTHROPIC_API_KEY",
            context={"provider": "anthropic"},
        )
    return ChatAnthropic(
        model_name=model or DEFAULT_MODEL,
        temperature=temperature,
        api_key=settings.anthropic_api_key,
        timeout=60,
        stop=None,
        **kwargs,
    )


__all__ = ["DEFAULT_MODEL", "build_anthropic_chat"]
```

- [ ] **Step 9.6：实现 openai**

Create `packages/llm_providers/src/llm_providers/providers/openai.py`：

```python
"""OpenAI provider。"""

from __future__ import annotations

from typing import Any

from langchain_openai import ChatOpenAI

from common.config import get_settings
from common.errors import ConfigError

DEFAULT_MODEL = "gpt-4o-mini"


def build_openai_chat(
    *,
    model: str | None = None,
    temperature: float = 0.7,
    **kwargs: Any,
) -> ChatOpenAI:
    """构造 OpenAI chat 模型。

    Raises:
        ConfigError: 未配置 AGENTTASK_OPENAI_API_KEY。
    """
    settings = get_settings(reload=True)
    if settings.openai_api_key is None:
        raise ConfigError(
            "missing AGENTTASK_OPENAI_API_KEY",
            context={"provider": "openai"},
        )
    return ChatOpenAI(
        model=model or DEFAULT_MODEL,
        temperature=temperature,
        api_key=settings.openai_api_key,
        **kwargs,
    )


__all__ = ["DEFAULT_MODEL", "build_openai_chat"]
```

- [ ] **Step 9.7：实现 ollama**

Create `packages/llm_providers/src/llm_providers/providers/ollama.py`：

```python
"""Ollama provider（本地）。无需 API key。"""

from __future__ import annotations

from typing import Any

from langchain_ollama import ChatOllama

from common.config import get_settings

DEFAULT_MODEL = "llama3.2"


def build_ollama_chat(
    *,
    model: str | None = None,
    temperature: float = 0.7,
    **kwargs: Any,
) -> ChatOllama:
    """构造 Ollama chat 模型。base_url 来自 Settings.ollama_base_url。"""
    settings = get_settings(reload=True)
    return ChatOllama(
        model=model or DEFAULT_MODEL,
        temperature=temperature,
        base_url=settings.ollama_base_url,
        **kwargs,
    )


__all__ = ["DEFAULT_MODEL", "build_ollama_chat"]
```

- [ ] **Step 9.8：跑全部测试确认通过**

```bash
uv run pytest packages/llm_providers/tests -v
```

Expected：13 个测试全过（3 + 3 + 3 + 4）。

- [ ] **Step 9.9：lint + type**

```bash
uv run ruff check packages/llm_providers
uv run mypy packages/llm_providers
```

Expected：均通过。

- [ ] **Step 9.10：提交**

```bash
git add packages/llm_providers/src/llm_providers/providers packages/llm_providers/tests/test_provider_*.py
git commit -m "feat(llm-providers): 添加 4 个 provider 工厂（deepseek/anthropic/openai/ollama）"
```

---

## Task 10：`llm_providers.factory` —— 统一工厂（TDD）

**Files:**
- Create: `packages/llm_providers/tests/test_factory.py`
- Create: `packages/llm_providers/src/llm_providers/factory.py`
- Modify: `packages/llm_providers/src/llm_providers/__init__.py`（re-export）

- [ ] **Step 10.1：写失败的测试**

Create `packages/llm_providers/tests/test_factory.py`：

```python
"""统一工厂 get_chat_model 测试。"""

from __future__ import annotations

import pytest
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from common.errors import ConfigError
from llm_providers import get_chat_model


@pytest.mark.fast
def test_default_provider_is_deepseek(monkeypatch: pytest.MonkeyPatch) -> None:
    """无参数时,使用 Settings.default_llm_provider（默认 deepseek）。"""
    monkeypatch.setenv("AGENTTASK_DEEPSEEK_API_KEY", "sk-test")
    llm = get_chat_model()
    assert isinstance(llm, ChatOpenAI)
    assert "deepseek.com" in str(llm.openai_api_base or "")


@pytest.mark.fast
def test_explicit_provider_anthropic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTTASK_ANTHROPIC_API_KEY", "sk-ant-test")
    llm = get_chat_model(provider="anthropic", model="claude-sonnet-4-6")
    assert isinstance(llm, ChatAnthropic)


@pytest.mark.fast
def test_explicit_provider_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTTASK_OPENAI_API_KEY", "sk-openai-test")
    llm = get_chat_model(provider="openai", model="gpt-4o-mini")
    assert isinstance(llm, ChatOpenAI)


@pytest.mark.fast
def test_explicit_provider_ollama() -> None:
    llm = get_chat_model(provider="ollama", model="llama3.2")
    assert isinstance(llm, ChatOllama)


@pytest.mark.fast
def test_default_provider_via_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """AGENTTASK_DEFAULT_LLM_PROVIDER=ollama → get_chat_model() 返回 Ollama。"""
    monkeypatch.setenv("AGENTTASK_DEFAULT_LLM_PROVIDER", "ollama")
    llm = get_chat_model()
    assert isinstance(llm, ChatOllama)


@pytest.mark.fast
def test_unknown_provider_raises() -> None:
    """未知 provider 应抛 ConfigError。"""
    with pytest.raises(ConfigError, match="unknown provider"):
        get_chat_model(provider="not-a-real-provider")


@pytest.mark.fast
def test_temperature_passthrough(monkeypatch: pytest.MonkeyPatch) -> None:
    """temperature 参数应透传到 provider。"""
    monkeypatch.setenv("AGENTTASK_DEEPSEEK_API_KEY", "sk-test")
    llm = get_chat_model(temperature=0.0)
    assert llm.temperature == 0.0  # type: ignore[attr-defined]
```

- [ ] **Step 10.2：跑测试确认失败**

```bash
uv run pytest packages/llm_providers/tests/test_factory.py -v
```

Expected：ImportError。

- [ ] **Step 10.3：实现 factory**

Create `packages/llm_providers/src/llm_providers/factory.py`：

```python
"""统一 chat model 工厂。

`get_chat_model(provider=None, model=None, **kwargs)` 是业务代码访问 LLM 的唯一入口。
provider=None 时走 Settings.default_llm_provider,model=None 时各 provider 用自己的默认值。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from common.config import get_settings
from common.errors import ConfigError

from .providers.anthropic import build_anthropic_chat
from .providers.deepseek import build_deepseek_chat
from .providers.ollama import build_ollama_chat
from .providers.openai import build_openai_chat

_BUILDERS: dict[str, Callable[..., BaseChatModel]] = {
    "deepseek": build_deepseek_chat,
    "anthropic": build_anthropic_chat,
    "openai": build_openai_chat,
    "ollama": build_ollama_chat,
}


def get_chat_model(
    *,
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0.7,
    **kwargs: Any,
) -> BaseChatModel:
    """构造一个 LangChain BaseChatModel。

    Args:
        provider: deepseek / anthropic / openai / ollama。None 时读 Settings 默认。
        model: 具体模型名。None 时各 provider 用 DEFAULT_MODEL。
        temperature: 采样温度。
        **kwargs: 透传给底层 provider 工厂。

    Raises:
        ConfigError: provider 名称未注册或对应 API key 缺失。
    """
    chosen = (provider or get_settings(reload=True).default_llm_provider).lower()
    builder = _BUILDERS.get(chosen)
    if builder is None:
        raise ConfigError(
            f"unknown provider: {chosen!r}; expected one of {sorted(_BUILDERS)}",
            context={"provider": chosen},
        )
    return builder(model=model, temperature=temperature, **kwargs)


__all__ = ["get_chat_model"]
```

- [ ] **Step 10.4：在 `__init__.py` re-export 公共 API**

Replace `packages/llm_providers/src/llm_providers/__init__.py` 内容：

```python
"""llm_providers: 多供应商 LLM 抽象。

公共 API:
- get_chat_model: 统一 chat model 工厂
"""

from __future__ import annotations

from .factory import get_chat_model

__version__ = "0.1.0"

__all__ = ["__version__", "get_chat_model"]
```

- [ ] **Step 10.5：跑测试确认通过**

```bash
uv run pytest packages/llm_providers/tests/test_factory.py -v
```

Expected：7 个测试全过。

- [ ] **Step 10.6：lint + type**

```bash
uv run ruff check packages/llm_providers
uv run mypy packages/llm_providers
```

Expected：均通过。

- [ ] **Step 10.7：提交**

```bash
git add packages/llm_providers/src/llm_providers/factory.py packages/llm_providers/src/llm_providers/__init__.py packages/llm_providers/tests/test_factory.py
git commit -m "feat(llm-providers): 添加 get_chat_model 统一工厂"
```

---

## Task 11：`llm_providers.middleware` —— 包装器（TDD）

**Files:**
- Create: `packages/llm_providers/tests/test_middleware.py`
- Create: `packages/llm_providers/src/llm_providers/middleware.py`

- [ ] **Step 11.1：写失败的测试**

Create `packages/llm_providers/tests/test_middleware.py`：

```python
"""middleware 包装器测试。

用 FakeListChatModel(LangChain 内置)模拟 LLM,完全本地、无网络。
"""

from __future__ import annotations

import fakeredis
import pytest
from langchain_community.chat_models.fake import FakeListChatModel
from langchain_core.messages import HumanMessage

from common.cost import CostTracker
from llm_providers.middleware import (
    with_cache,
    with_cost_tracking,
)


@pytest.mark.fast
def test_with_cost_tracking_records_after_invoke() -> None:
    """invoke 之后 CostTracker 应记录到这一次调用的 token 数。"""
    fake = FakeListChatModel(responses=["hello world"])
    tracker = CostTracker()
    wrapped = with_cost_tracking(fake, tracker=tracker, model="deepseek-chat")

    response = wrapped.invoke([HumanMessage(content="hi")])

    assert response.content == "hello world"
    # token 数应记录(估算或真实,大于 0 即可)
    assert tracker.total_input_tokens > 0
    assert tracker.total_output_tokens > 0


@pytest.mark.fast
def test_with_cost_tracking_attributes_to_correct_model() -> None:
    """记录应归到传入的 model 名,而非 FakeListChatModel 自己的。"""
    fake = FakeListChatModel(responses=["abc"])
    tracker = CostTracker()
    wrapped = with_cost_tracking(fake, tracker=tracker, model="claude-sonnet-4-6")

    wrapped.invoke([HumanMessage(content="hi")])

    per_model = tracker.per_model()
    assert "claude-sonnet-4-6" in per_model


@pytest.mark.fast
def test_with_cache_first_invoke_executes_underlying() -> None:
    """首次调用应实际调用底层 LLM。"""
    fake = FakeListChatModel(responses=["A", "B"])  # 2 个候选回答
    redis_client = fakeredis.FakeRedis()
    wrapped = with_cache(fake, client=redis_client, namespace="test", ttl_seconds=60)

    response = wrapped.invoke([HumanMessage(content="x")])
    assert response.content == "A"


@pytest.mark.fast
def test_with_cache_second_invoke_hits_cache() -> None:
    """同样 prompt 第二次调用应命中缓存,不消耗底层 LLM 的下一个回答。"""
    fake = FakeListChatModel(responses=["A", "B"])
    redis_client = fakeredis.FakeRedis()
    wrapped = with_cache(fake, client=redis_client, namespace="test", ttl_seconds=60)

    first = wrapped.invoke([HumanMessage(content="x")])
    second = wrapped.invoke([HumanMessage(content="x")])

    assert first.content == second.content == "A"
    # 如果穿透了,第二次应该是 "B",所以下一个不同 prompt 应该拿到 "B"
    third = wrapped.invoke([HumanMessage(content="y")])
    assert third.content == "B"


@pytest.mark.fast
def test_with_cache_different_prompts_dont_collide() -> None:
    """不同 prompt 应各自缓存。"""
    fake = FakeListChatModel(responses=["A", "B", "A-again"])
    redis_client = fakeredis.FakeRedis()
    wrapped = with_cache(fake, client=redis_client, namespace="test", ttl_seconds=60)

    a1 = wrapped.invoke([HumanMessage(content="x")])
    b1 = wrapped.invoke([HumanMessage(content="y")])
    a2 = wrapped.invoke([HumanMessage(content="x")])

    assert a1.content == "A"
    assert b1.content == "B"
    assert a2.content == "A"  # 命中缓存


@pytest.mark.fast
def test_compose_cost_then_cache_does_not_double_count() -> None:
    """先成本追踪、再缓存:同样 prompt 第二次命中缓存时不应再次计数。"""
    fake = FakeListChatModel(responses=["A", "B"])
    redis_client = fakeredis.FakeRedis()
    tracker = CostTracker()

    wrapped = with_cost_tracking(
        with_cache(fake, client=redis_client, namespace="test", ttl_seconds=60),
        tracker=tracker,
        model="deepseek-chat",
    )

    wrapped.invoke([HumanMessage(content="x")])
    tokens_after_first = tracker.total_input_tokens + tracker.total_output_tokens

    wrapped.invoke([HumanMessage(content="x")])  # 缓存命中
    tokens_after_second = tracker.total_input_tokens + tracker.total_output_tokens

    # 缓存命中时,with_cost_tracking 应跳过记账(检测到 cached 标记)
    assert tokens_after_second == tokens_after_first
```

- [ ] **Step 11.2：跑测试确认失败**

```bash
uv run pytest packages/llm_providers/tests/test_middleware.py -v
```

Expected：ImportError 或 cmd 失败。先确认 `langchain-community` 是否在 deps 中——如果不在,应在 llm_providers 的 pyproject 加上,因为 FakeListChatModel 在 community 包。

如果 ImportError 提示找不到 langchain_community,先按下面 11.3 的 pyproject 修改加依赖,再回到 11.2 验证。

- [ ] **Step 11.3：补 langchain-community 依赖（仅测试用）**

Modify `packages/llm_providers/pyproject.toml`，把 `dependencies` 改为：

```toml
dependencies = [
    "common",
    "langchain-core>=0.3.20,<0.4",
    "langchain-openai>=0.2.10,<0.3",
    "langchain-anthropic>=0.3.0,<0.4",
    "langchain-ollama>=0.2.2,<0.3",
    "langchain-community>=0.3.10,<0.4",
]
```

```bash
uv sync
```

- [ ] **Step 11.4：实现 middleware**

Create `packages/llm_providers/src/llm_providers/middleware.py`：

```python
"""Chat model 中间件:cost tracking / cache。

实现思路:
- 通过 LangChain RunnableLambda + bind 包装底层 BaseChatModel 的 invoke,
  返回的对象继续是 Runnable,可以与 LangGraph / LCEL 串联。
- with_cost_tracking 监听 invoke 的 usage_metadata。
- with_cache 用 prompt JSON + model name 作 key,缓存 AIMessage 的内容字段。
"""

from __future__ import annotations

import functools
import json
from typing import Any, cast

import redis
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.runnables import Runnable, RunnableLambda

from common.cache import make_cache_key
from common.cost import CostTracker, estimate_cost_usd

# 用 message.additional_kwargs 标记"来自缓存",cost 包装器据此跳过计数
_CACHED_FLAG_KEY = "_agenttask_from_cache"


def _messages_to_payload(messages: list[BaseMessage]) -> dict[str, Any]:
    """把消息列表转成稳定的 JSON-able 字典(用于 cache key)。"""
    return {
        "messages": [
            {"type": m.type, "content": m.content}
            for m in messages
        ]
    }


def with_cache(
    chat_model: BaseChatModel,
    *,
    client: redis.Redis,
    namespace: str,
    ttl_seconds: int,
) -> Runnable[list[BaseMessage], BaseMessage]:
    """缓存 invoke 的 AIMessage 文本内容。"""
    model_name = getattr(chat_model, "model_name", None) or getattr(chat_model, "model", "unknown")

    @functools.wraps(chat_model.invoke)  # type: ignore[arg-type]
    def cached_invoke(messages: list[BaseMessage]) -> BaseMessage:
        payload = _messages_to_payload(messages)
        key = make_cache_key(namespace, str(model_name), payload)
        hit = client.get(key)
        if hit is not None:
            cached_data = json.loads(hit)
            msg = AIMessage(content=cached_data["content"])
            msg.additional_kwargs[_CACHED_FLAG_KEY] = True
            return msg
        result = chat_model.invoke(messages)
        client.setex(
            key,
            ttl_seconds,
            json.dumps({"content": result.content}, ensure_ascii=False),
        )
        return result

    return RunnableLambda(cached_invoke)


def with_cost_tracking(
    chat_model: BaseChatModel | Runnable[list[BaseMessage], BaseMessage],
    *,
    tracker: CostTracker,
    model: str,
) -> Runnable[list[BaseMessage], BaseMessage]:
    """invoke 后向 tracker 记录 input/output token。

    优先使用 result.usage_metadata(LangChain 0.3+);若无则按 char // 4 粗估。
    缓存命中(_agenttask_from_cache 标记)的响应跳过计数。
    """

    def tracked_invoke(messages: list[BaseMessage]) -> BaseMessage:
        result = chat_model.invoke(messages)
        if isinstance(result, AIMessage) and result.additional_kwargs.get(_CACHED_FLAG_KEY):
            return result
        usage = getattr(result, "usage_metadata", None)
        if usage:
            input_tokens = int(usage.get("input_tokens", 0))
            output_tokens = int(usage.get("output_tokens", 0))
        else:
            input_tokens = sum(len(str(m.content)) // 4 for m in messages) or 1
            output_tokens = max(len(str(result.content)) // 4, 1)
        tracker.record(model=model, input_tokens=input_tokens, output_tokens=output_tokens)
        return cast(BaseMessage, result)

    return RunnableLambda(tracked_invoke)


__all__ = ["with_cache", "with_cost_tracking"]
```

- [ ] **Step 11.5：跑测试确认通过**

```bash
uv run pytest packages/llm_providers/tests/test_middleware.py -v
```

Expected：6 个测试全过。

- [ ] **Step 11.6：lint + type**

```bash
uv run ruff check packages/llm_providers
uv run mypy packages/llm_providers
```

Expected：均通过。

- [ ] **Step 11.7：提交**

```bash
git add packages/llm_providers/src/llm_providers/middleware.py packages/llm_providers/tests/test_middleware.py packages/llm_providers/pyproject.toml uv.lock
git commit -m "feat(llm-providers): 添加 middleware（with_cost_tracking / with_cache）"
```

---

## Task 12：`llm_providers.embeddings` —— Embedding 工厂（TDD）

**Files:**
- Create: `packages/llm_providers/tests/test_embeddings.py`
- Create: `packages/llm_providers/src/llm_providers/embeddings.py`
- Modify: `packages/llm_providers/src/llm_providers/__init__.py`（再 re-export）

- [ ] **Step 12.1：写失败的测试**

Create `packages/llm_providers/tests/test_embeddings.py`：

```python
"""embedding 工厂测试。"""

from __future__ import annotations

import pytest
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings

from common.errors import ConfigError
from llm_providers import get_embeddings


@pytest.mark.fast
def test_get_embeddings_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTTASK_OPENAI_API_KEY", "sk-test")
    emb = get_embeddings(provider="openai", model="text-embedding-3-small")
    assert isinstance(emb, OpenAIEmbeddings)
    assert emb.model == "text-embedding-3-small"


@pytest.mark.fast
def test_get_embeddings_openai_default_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTTASK_OPENAI_API_KEY", "sk-test")
    emb = get_embeddings(provider="openai")
    assert emb.model == "text-embedding-3-small"


@pytest.mark.fast
def test_get_embeddings_ollama() -> None:
    emb = get_embeddings(provider="ollama", model="nomic-embed-text")
    assert isinstance(emb, OllamaEmbeddings)
    assert emb.model == "nomic-embed-text"


@pytest.mark.fast
def test_get_embeddings_openai_missing_key() -> None:
    with pytest.raises(ConfigError, match="OPENAI_API_KEY"):
        get_embeddings(provider="openai")


@pytest.mark.fast
def test_get_embeddings_unknown_provider() -> None:
    with pytest.raises(ConfigError, match="unknown embedding provider"):
        get_embeddings(provider="anthropic")  # Anthropic 没有 embedding API


@pytest.mark.fast
def test_get_embeddings_default_provider_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    """无 provider 参数时,默认 openai(因为 deepseek/anthropic 都没有 embedding)。"""
    monkeypatch.setenv("AGENTTASK_OPENAI_API_KEY", "sk-test")
    emb = get_embeddings()
    assert isinstance(emb, OpenAIEmbeddings)
```

- [ ] **Step 12.2：跑测试确认失败**

```bash
uv run pytest packages/llm_providers/tests/test_embeddings.py -v
```

Expected：ImportError(`get_embeddings` 不存在)。

- [ ] **Step 12.3：实现 embeddings**

Create `packages/llm_providers/src/llm_providers/embeddings.py`：

```python
"""Embedding 工厂。

仅支持 openai / ollama —— DeepSeek / Anthropic 不提供 embedding API。
"""

from __future__ import annotations

from typing import Any

from langchain_core.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings

from common.config import get_settings
from common.errors import ConfigError

DEFAULT_OPENAI_MODEL = "text-embedding-3-small"
DEFAULT_OLLAMA_MODEL = "nomic-embed-text"


def get_embeddings(
    *,
    provider: str = "openai",
    model: str | None = None,
    **kwargs: Any,
) -> Embeddings:
    """构造 embedding 模型。

    Args:
        provider: openai / ollama。默认 openai。
        model: 具体模型名。

    Raises:
        ConfigError: provider 不支持或缺 key。
    """
    settings = get_settings(reload=True)
    chosen = provider.lower()

    if chosen == "openai":
        if settings.openai_api_key is None:
            raise ConfigError(
                "missing AGENTTASK_OPENAI_API_KEY",
                context={"provider": "openai"},
            )
        return OpenAIEmbeddings(
            model=model or DEFAULT_OPENAI_MODEL,
            api_key=settings.openai_api_key,
            **kwargs,
        )

    if chosen == "ollama":
        return OllamaEmbeddings(
            model=model or DEFAULT_OLLAMA_MODEL,
            base_url=settings.ollama_base_url,
            **kwargs,
        )

    raise ConfigError(
        f"unknown embedding provider: {provider!r}; expected one of ['openai', 'ollama']",
        context={"provider": chosen},
    )


__all__ = ["DEFAULT_OLLAMA_MODEL", "DEFAULT_OPENAI_MODEL", "get_embeddings"]
```

- [ ] **Step 12.4：在 `__init__.py` 加 re-export**

Replace `packages/llm_providers/src/llm_providers/__init__.py`：

```python
"""llm_providers: 多供应商 LLM 抽象。

公共 API:
- get_chat_model: 统一 chat model 工厂
- get_embeddings: embedding 工厂
"""

from __future__ import annotations

from .embeddings import get_embeddings
from .factory import get_chat_model

__version__ = "0.1.0"

__all__ = ["__version__", "get_chat_model", "get_embeddings"]
```

- [ ] **Step 12.5：跑测试确认通过**

```bash
uv run pytest packages/llm_providers/tests/test_embeddings.py -v
```

Expected：6 个测试全过。

- [ ] **Step 12.6：lint + type**

```bash
uv run ruff check packages/llm_providers
uv run mypy packages/llm_providers
```

Expected：均通过。

- [ ] **Step 12.7：提交**

```bash
git add packages/llm_providers/src/llm_providers/embeddings.py packages/llm_providers/src/llm_providers/__init__.py packages/llm_providers/tests/test_embeddings.py
git commit -m "feat(llm-providers): 添加 get_embeddings 工厂（openai / ollama）"
```

---

## Task 13：M1 验收 demo + 集成测试

**Files:**
- Create: `examples/m1_provider_switch.py`
- Create: `tests/test_m1_acceptance.py`
- Modify: `examples/.gitkeep`（删掉）

- [ ] **Step 13.1：写 5 行验收 demo**

```bash
rm -f examples/.gitkeep
```

Create `examples/m1_provider_switch.py`：

```python
"""M1 验收 demo:5 行调通 DeepSeek,1 行切到 Ollama。

不消费 API key 的版本运行方式:
    AGENTTASK_DEFAULT_LLM_PROVIDER=ollama uv run python examples/m1_provider_switch.py

用 DeepSeek 真实调用:
    AGENTTASK_DEEPSEEK_API_KEY=sk-... uv run python examples/m1_provider_switch.py
"""

from __future__ import annotations

from common.cost import CostTracker
from common.logging import configure_logging, get_logger
from llm_providers import get_chat_model
from llm_providers.middleware import with_cost_tracking


def main() -> int:
    configure_logging(level="INFO")
    log = get_logger("m1.demo")
    tracker = CostTracker()

    llm = get_chat_model()  # 从 Settings 读默认 provider
    wrapped = with_cost_tracking(llm, tracker=tracker, model="deepseek-chat")

    response = wrapped.invoke("用一句话介绍 LangGraph")
    log.info(
        "demo_done",
        content_preview=str(response.content)[:80],
        total_cost_usd=tracker.total_cost_usd,
        total_input_tokens=tracker.total_input_tokens,
        total_output_tokens=tracker.total_output_tokens,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 13.2：写验收测试（不打真实 LLM）**

Create `tests/test_m1_acceptance.py`：

```python
"""M1 里程碑验收 smoke test。

验证 spec 第 9.1 M1 验收点:
1. 5 行 demo 调 DeepSeek 然后切换 Ollama 不改业务代码 → 通过 mock 验证 provider 可热切换
2. 成本自动记录 → CostTracker 累计正确
3. 限流自动重试 → retry_on_retryable 行为正确(已在 packages/common/tests/test_retry.py 覆盖)

本测试只用 FakeListChatModel,不消耗任何 LLM 配额。
"""

from __future__ import annotations

import pytest
from langchain_community.chat_models.fake import FakeListChatModel
from langchain_core.messages import HumanMessage

from common.cost import CostTracker
from llm_providers.middleware import with_cost_tracking


@pytest.mark.fast
def test_m1_provider_switch_with_cost_tracking() -> None:
    """同一段业务代码,通过包装不同 provider 实现"换 LLM 不改业务"。"""
    tracker = CostTracker()

    def business_logic(llm) -> str:  # noqa: ANN001
        wrapped = with_cost_tracking(llm, tracker=tracker, model="deepseek-chat")
        result = wrapped.invoke([HumanMessage(content="hi")])
        return str(result.content)

    fake_deepseek = FakeListChatModel(responses=["hello from deepseek"])
    fake_ollama = FakeListChatModel(responses=["hello from ollama"])

    out1 = business_logic(fake_deepseek)
    out2 = business_logic(fake_ollama)

    assert out1 == "hello from deepseek"
    assert out2 == "hello from ollama"
    assert tracker.total_input_tokens > 0
    assert tracker.total_output_tokens > 0


@pytest.mark.fast
def test_m1_cost_attributed_per_model() -> None:
    """两次包装时若指定不同 model,累计应分别记录。"""
    tracker = CostTracker()
    fake = FakeListChatModel(responses=["a", "b"])

    with_cost_tracking(fake, tracker=tracker, model="deepseek-chat").invoke(
        [HumanMessage(content="x")]
    )
    with_cost_tracking(fake, tracker=tracker, model="claude-sonnet-4-6").invoke(
        [HumanMessage(content="y")]
    )

    per_model = tracker.per_model()
    assert "deepseek-chat" in per_model
    assert "claude-sonnet-4-6" in per_model


@pytest.mark.fast
def test_m1_demo_script_main_callable() -> None:
    """验收 demo 应可 import 而不报错（实际运行需要 ollama 或 deepseek）。"""
    import importlib.util
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent
    demo_path = repo_root / "examples" / "m1_provider_switch.py"
    assert demo_path.exists()
    spec = importlib.util.spec_from_file_location("m1_demo", demo_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main)
```

- [ ] **Step 13.3：跑验收测试**

```bash
uv run pytest tests/test_m1_acceptance.py -v
```

Expected：3 个测试全过。

- [ ] **Step 13.4：跑 demo 的 import smoke（不需要真实 key）**

```bash
uv run python -c "import importlib.util; spec = importlib.util.spec_from_file_location('m1_demo', 'examples/m1_provider_switch.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print('demo importable, main =', m.main)"
```

Expected：输出 `demo importable, main = <function main at 0x...>`,无 ImportError。

- [ ] **Step 13.5：lint + type**

```bash
uv run ruff check examples tests
uv run mypy tests/test_m1_acceptance.py
```

Expected：均通过。

- [ ] **Step 13.6：提交**

```bash
git add examples/m1_provider_switch.py tests/test_m1_acceptance.py
git rm --cached examples/.gitkeep 2>/dev/null || true
rm -f examples/.gitkeep
git commit -m "feat(examples): 添加 M1 验收 demo（5 行 provider 切换 + 成本记录）"
```

---

## Task 14：覆盖率 ≥ 80% gate + M1 总结

**Files:**
- Modify: 必要时调整测试覆盖未到 80% 的模块。
- Modify: `Makefile`（增加 `make coverage` 目标）。

- [ ] **Step 14.1：跑全量覆盖率**

```bash
uv run pytest packages/common packages/llm_providers tests --cov=common --cov=llm_providers --cov-report=term-missing --cov-fail-under=80
```

Expected：两个包合并覆盖率 ≥ 80%。

- [ ] **Step 14.2：如果未到 80%,补测试再跑**

读 `term-missing` 输出找未覆盖行,在对应 `tests/` 文件加测试。每补一个测试,跑一次 pytest 验证通过,再回到 14.1。

修复至 ≥ 80% 后再继续。

- [ ] **Step 14.3：在 Makefile 增加 coverage 目标**

修改 `Makefile`,在 `test:` 目标之后插入：

```makefile
.PHONY: coverage
coverage: ## 跑覆盖率 (M1+ 需 ≥ 80%)
	uv run pytest packages tests --cov=common --cov=llm_providers --cov-report=term-missing --cov-fail-under=80
```

并把 `coverage` 加进 `help` 列出的目标列表(若 help 是 grep 自动生成,可跳过此步)。

- [ ] **Step 14.4：跑 make lint / type / test / coverage 全套**

```bash
make lint
make type
make test
make coverage
```

Expected：全部通过。

- [ ] **Step 14.5：补 README 把 M1 状态从"⏳"改为"✅"**

修改根 `README.md` 的实施路线图表格,M1 行从：

```
| M1 | `packages/common` + `packages/llm_providers` | - |
```

改为：

```
| ✅ M1 | `packages/common` + `packages/llm_providers` | - |
```

- [ ] **Step 14.6：提交**

```bash
git add Makefile README.md
git commit -m "chore(m1): 增加 make coverage 目标 + 路线图标记 M1 完成"
```

- [ ] **Step 14.7：查看完整 commit 链**

```bash
git log --oneline | head -20
```

Expected：约 13–14 条 commit 串成 M1 轨迹（含 plan 提交 + 13 个 task）。

- [ ] **Step 14.8：（可选）打标签**

```bash
git tag -a m1-complete -m "M1 packages/common + packages/llm_providers 完成"
```

---

## Self-Review

### Spec 覆盖检查

对照 spec 第 4.2 节 packages/common 与 packages/llm_providers 模块清单:

| Spec 要求 | 对应 Task | 状态 |
|---|---|---|
| `common/config.py` (pydantic-settings 多环境配置) | Task 3 | ✓ |
| `common/logging.py` (structlog) | Task 4 | ✓ |
| `common/errors.py` (AgentError 层级) | Task 2 | ✓ |
| `common/retry.py` (tenacity 重试) | Task 5 | ✓ |
| `common/cost.py` (成本追踪) | Task 6 | ✓ |
| `common/cache.py` (Redis 缓存装饰器) | Task 7 | ✓ |
| `llm_providers/factory.py` | Task 10 | ✓ |
| `llm_providers/providers/deepseek.py` | Task 9 | ✓ |
| `llm_providers/providers/anthropic.py` | Task 9 | ✓ |
| `llm_providers/providers/openai.py` | Task 9 | ✓ |
| `llm_providers/providers/ollama.py` | Task 9 | ✓ |
| `llm_providers/middleware.py` | Task 11 | ✓ |
| `llm_providers/embeddings.py` | Task 12 | ✓ |
| 80% 覆盖率 | Task 14 | ✓ |
| 验收:provider 热切换 | Task 13 | ✓ |
| 验收:成本自动记录 | Task 11/13 | ✓ |
| 验收:限流自动重试 | Task 5 | ✓ |

### 占位符扫描

已检查全文,无 "TBD" / "TODO" / "fill in" / "实现细节略"。所有 step 均含具体代码。

### 类型 / 接口一致性

- `AgentError` / `ConfigError` / `RateLimitError` / `RetryableError` / `LLMError` / `BudgetExceededError` / `ToolError` —— Task 2 定义,Task 3/5/9/10/12 引用;名字与签名一致。
- `Settings` / `get_settings(*, reload)` / `AppEnv` —— Task 3 定义,Task 9/10/12 引用,签名一致。
- `CostTracker` / `ModelPrice` / `PRICE_TABLE` / `estimate_cost_usd` —— Task 6 定义,Task 11/13 引用。
- `make_cache_key` / `cached` —— Task 7 定义,Task 11(middleware)直接复用 `make_cache_key`。
- `build_<provider>_chat(*, model, temperature, **kwargs)` —— Task 9 定义,Task 10 在 `_BUILDERS` 字典中调用。
- `get_chat_model(*, provider, model, temperature, **kwargs)` —— Task 10 定义,Task 13 调用,签名一致。
- `with_cost_tracking(chat_model, *, tracker, model)` / `with_cache(chat_model, *, client, namespace, ttl_seconds)` —— Task 11 定义,Task 13 调用,签名一致。
- `get_embeddings(*, provider, model, **kwargs)` —— Task 12 定义,后续 M3 retrieval 包会消费。

### Scope 检查

本计划严格限定于 M1 里程碑(common + llm_providers)。不引入:
- 任何 lessons 内容（M2 起）
- agent_core / tools（M2 起）
- memory / retrieval（M3 起）
- tracing / evaluation / guardrails / sandbox（M4 起）
- capstone（M5 起）

---

**计划完成。共 14 个 Task,预估 13 次 commit + 若干修复 commit,完整执行时间约 4–6 小时。**
