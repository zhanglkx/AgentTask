"""LLM 成本追踪。

PRICE_TABLE 为 2026-06 时点参考价(USD per 1M tokens)。后续里程碑可改为
读取 YAML/JSON 配置文件,目前 inline dict 已足够。

未知模型成本计为 0(避免日志/链路炸掉),由调用方决定是否警告。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .errors import BudgetExceededError


@dataclass(frozen=True, slots=True)
class ModelPrice:
    """单模型价格(USD per 1M tokens)。"""

    input_per_1m_usd: float
    output_per_1m_usd: float


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
            raise BudgetExceededError(spent_usd=self.total_cost_usd, limit_usd=self.budget_usd)


__all__ = ["PRICE_TABLE", "CostTracker", "ModelPrice", "estimate_cost_usd"]
