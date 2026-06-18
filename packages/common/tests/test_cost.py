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
    t.check_budget()


@pytest.mark.fast
def test_cost_tracker_budget_exceeded_raises() -> None:
    """超预算 → 抛 BudgetExceededError。"""
    t = CostTracker(budget_usd=0.0001)
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
    t.check_budget()


@pytest.mark.fast
def test_model_price_is_frozen() -> None:
    """ModelPrice 应不可变,防止运行时被改坏价格表。"""
    price = ModelPrice(input_per_1m_usd=1.0, output_per_1m_usd=2.0)
    with pytest.raises((AttributeError, TypeError)):
        price.input_per_1m_usd = 999  # type: ignore[misc]
