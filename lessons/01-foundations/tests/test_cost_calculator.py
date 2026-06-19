"""cost_calculator 测试：token 计费纯数学测试。"""

from __future__ import annotations

import pytest

from cost_calculator import PRICING_TABLE, PricingEntry, calculate_cost


@pytest.mark.fast
def test_calculate_cost_basic() -> None:
    """基本计费计算：input * price_in + output * price_out。"""
    pricing = PricingEntry(
        model="test-model",
        price_per_input_token=0.00001,
        price_per_output_token=0.00003,
    )
    cost = calculate_cost(
        input_tokens=1000,
        output_tokens=500,
        pricing=pricing,
    )
    assert cost == pytest.approx(0.01 + 0.015, abs=1e-6)


@pytest.mark.fast
def test_calculate_cost_zero_tokens() -> None:
    """零 token → 零成本。"""
    pricing = PricingEntry(
        model="free-model",
        price_per_input_token=0.0,
        price_per_output_token=0.0,
    )
    assert calculate_cost(input_tokens=0, output_tokens=0, pricing=pricing) == 0.0


@pytest.mark.fast
def test_pricing_table_has_known_models() -> None:
    """PRICING_TABLE 应包含 deepseek-chat 和 gpt-4o。"""
    assert "deepseek-chat" in PRICING_TABLE
    assert "gpt-4o" in PRICING_TABLE


@pytest.mark.fast
def test_pricing_table_values_reasonable() -> None:
    """DeepSeek 价格应远低于 GPT-4o（核心卖点）。"""
    ds = PRICING_TABLE["deepseek-chat"]
    gpt = PRICING_TABLE["gpt-4o"]
    assert ds.price_per_input_token < gpt.price_per_input_token
    assert ds.price_per_output_token < gpt.price_per_output_token


@pytest.mark.fast
def test_calculate_cost_with_pricing_table() -> None:
    """从 PRICING_TABLE 取定价并计算成本。"""
    cost = calculate_cost(
        input_tokens=1000,
        output_tokens=200,
        pricing=PRICING_TABLE["deepseek-chat"],
    )
    assert cost > 0
