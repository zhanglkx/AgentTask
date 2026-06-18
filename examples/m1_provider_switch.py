"""M1 验收 demo:5 行调通 DeepSeek,1 行切到 Ollama。

不消费 API key 的版本运行方式:
    AGENTTASK_DEFAULT_LLM_PROVIDER=ollama uv run python examples/m1_provider_switch.py

用 DeepSeek 真实调用:
    AGENTTASK_DEEPSEEK_API_KEY=sk-... uv run python examples/m1_provider_switch.py
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from common.cost import CostTracker
from common.logging import configure_logging, get_logger
from llm_providers import get_chat_model
from llm_providers.middleware import with_cost_tracking


def main() -> int:
    configure_logging(level="INFO")
    log = get_logger("m1.demo")
    tracker = CostTracker()

    llm = get_chat_model()  # 从 Settings 读默认 provider
    wrapped = with_cost_tracking(llm, tracker=tracker, model="deepseek-chat")

    response = wrapped.invoke([HumanMessage(content="用一句话介绍 LangGraph")])
    log.info(
        "demo_done",
        content_preview=str(response.content)[:80],
        total_cost_usd=tracker.total_cost_usd,
        total_input_tokens=tracker.total_input_tokens,
        total_output_tokens=tracker.total_output_tokens,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
