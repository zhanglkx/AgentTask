"""练习 1：计算不同模型的 token 计费。

任务:
1. 用 calculate_cost 计算 claude-sonnet-4-6 处理 5000 input + 1000 output 的成本
2. 对比三个模型（deepseek / gpt-4o / claude）的价格差异
3. 如果每天调 1000 次，每次 200 input + 50 output，一个月（30 天）总成本是多少？

提示:
- 从 PRICING_TABLE 取 PricingEntry
- 用 calculate_cost 函数
"""

from __future__ import annotations


def exercise_1_model_comparison() -> dict[str, float]:
    """对比三个模型处理 5000 input + 1000 output 的成本。"""
    # TODO: 填写代码
    results: dict[str, float] = {}
    for _model_name in ["deepseek-chat", "gpt-4o", "claude-sonnet-4-6"]:
        # TODO: results[_model_name] = calculate_cost(...)
        pass
    return results


def exercise_1_monthly_cost(model: str = "deepseek-chat") -> float:
    """计算每天 1000 次（200 in + 50 out）× 30 天的总成本。"""
    # TODO: 填写代码
    pass
