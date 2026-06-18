"""Chat model 中间件:cost tracking / cache。

实现思路:
- 通过 LangChain RunnableLambda 包装底层 BaseChatModel 的 invoke,
  返回的对象继续是 Runnable,可以与 LangGraph / LCEL 串联。
- with_cost_tracking 监听 invoke 的 usage_metadata。
- with_cache 用 prompt JSON + model name 作 key,缓存 AIMessage 的内容字段。
"""

from __future__ import annotations

import json
from typing import Any

import redis
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.runnables import Runnable, RunnableLambda

from common.cache import make_cache_key
from common.cost import CostTracker

# 用 message.additional_kwargs 标记"来自缓存",cost 包装器据此跳过计数
_CACHED_FLAG_KEY = "_agenttask_from_cache"


def _messages_to_payload(messages: list[BaseMessage]) -> dict[str, Any]:
    """把消息列表转成稳定的 JSON-able 字典(用于 cache key)。"""
    return {"messages": [{"type": m.type, "content": m.content} for m in messages]}


def with_cache(
    chat_model: BaseChatModel,
    *,
    client: redis.Redis,
    namespace: str,
    ttl_seconds: int,
) -> Runnable[list[BaseMessage], BaseMessage]:
    """缓存 invoke 的 AIMessage 文本内容。"""
    model_name = getattr(chat_model, "model_name", None) or getattr(chat_model, "model", "unknown")

    def cached_invoke(messages: list[BaseMessage], **_: Any) -> BaseMessage:
        payload = _messages_to_payload(messages)
        key = make_cache_key(namespace, str(model_name), payload)
        hit = client.get(key)
        if hit is not None and isinstance(hit, bytes | bytearray | str):
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

    def tracked_invoke(messages: list[BaseMessage], **_: Any) -> BaseMessage:
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
        return result

    return RunnableLambda(tracked_invoke)


__all__ = ["with_cache", "with_cost_tracking"]
