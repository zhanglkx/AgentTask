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
