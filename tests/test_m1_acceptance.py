"""M1 里程碑验收 smoke test。

验证 spec 第 9.1 M1 验收点:
1. 5 行 demo 调 DeepSeek 然后切换 Ollama 不改业务代码 → 通过 mock 验证 provider 可热切换
2. 成本自动记录 → CostTracker 累计正确
3. 限流自动重试 → retry_on_retryable 行为正确(已在 packages/common/tests/test_retry.py 覆盖)

本测试只用 FakeListChatModel,不消耗任何 LLM 配额。
"""

from __future__ import annotations

from typing import Any

import pytest
from langchain_community.chat_models.fake import FakeListChatModel
from langchain_core.messages import HumanMessage

from common.cost import CostTracker
from llm_providers.middleware import with_cost_tracking


@pytest.mark.fast
def test_m1_provider_switch_with_cost_tracking() -> None:
    """同一段业务代码,通过包装不同 provider 实现"换 LLM 不改业务"。"""
    tracker = CostTracker()

    def business_logic(llm: Any) -> str:
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
