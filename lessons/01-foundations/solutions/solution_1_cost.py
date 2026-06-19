"""练习 1 答案：计算不同模型的 token 计费。"""

from __future__ import annotations

from cost_calculator import PRICING_TABLE, calculate_cost


def exercise_1_model_comparison() -> dict[str, float]:
    """对比三个模型处理 5000 input + 1000 output 的成本。"""
    results: dict[str, float] = {}
    for model_name in ["deepseek-chat", "gpt-4o", "claude-sonnet-4-6"]:
        results[model_name] = calculate_cost(5000, 1000, PRICING_TABLE[model_name])
    return results


def exercise_1_monthly_cost(model: str = "deepseek-chat") -> float:
    """计算每天 1000 次（200 in + 50 out）× 30 天的总成本。"""
    per_call = calculate_cost(200, 50, PRICING_TABLE[model])
    return per_call * 1000 * 30
