"""Token 计费计算器。

公式:
    cost = input_tokens × price_per_input_token + output_tokens × price_per_output_token

类比前端:
    - token ≈ UTF-8 code point（但粒度更粗,1 token ≈ 0.75 英文单词）
    - 计费 ≈ 云函数按调用计费（AWS Lambda 的 $/invocation）
"""

from __future__ import annotations

from pydantic import BaseModel


class PricingEntry(BaseModel):
    """单个模型的定价信息。"""

    model: str
    price_per_input_token: float  # USD / token
    price_per_output_token: float  # USD / token


# 2025-2026 大厂主流模型定价（单位: USD/token）
# 来源: 各供应商官网,注意价格可能变动,此处仅作教学示例
PRICING_TABLE: dict[str, PricingEntry] = {
    "deepseek-chat": PricingEntry(
        model="deepseek-chat",
        price_per_input_token=0.00000014,  # $0.14/M input tokens
        price_per_output_token=0.00000028,  # $0.28/M output tokens
    ),
    "gpt-4o": PricingEntry(
        model="gpt-4o",
        price_per_input_token=0.0000025,  # $2.50/M input tokens
        price_per_output_token=0.00001,  # $10/M output tokens
    ),
    "claude-sonnet-4-6": PricingEntry(
        model="claude-sonnet-4-6",
        price_per_input_token=0.000003,  # $3/M input tokens
        price_per_output_token=0.000015,  # $15/M output tokens
    ),
}


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    pricing: PricingEntry,
) -> float:
    """计算 token 计费金额。

    Args:
        input_tokens: 输入 token 数量。
        output_tokens: 输出 token 数量。
        pricing: 该模型的定价信息。

    Returns:
        总成本（USD）。
    """
    return (
        input_tokens * pricing.price_per_input_token
        + output_tokens * pricing.price_per_output_token
    )
