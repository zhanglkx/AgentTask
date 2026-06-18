"""llm_providers: 多供应商 LLM 抽象。

公共 API:
- get_chat_model: 统一 chat model 工厂
"""

from __future__ import annotations

from .factory import get_chat_model

__version__ = "0.1.0"

__all__ = ["__version__", "get_chat_model"]
