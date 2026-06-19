"""写作 agent：写 → critic → 修订循环。

类比前端:
    - Generator ≈ Feature developer（写初版代码）
    - Critic ≈ Code reviewer（指出问题）
    - ACCEPT marker ≈ CI passing（"可以合并了"）

核心思路:
    1. generator 写初版（draft）
    2. critic 批判（ACCEPT 或指出问题）
    3. 如果 ACCEPT → 返回 draft
    4. 如果不是 → generator 修订 → critic 再审 → 循环
    5. 超过 max_iterations → 返回最后一次 draft

对比 agent_core.build_reflection_graph:
    手写版看清底层，prebuilt 版封装标准模式。
"""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage


def run_writing_agent(
    generator_llm: BaseChatModel,
    critic_llm: BaseChatModel,
    task: str,
    *,
    max_iterations: int = 3,
    accept_marker: str = "ACCEPT",
) -> dict[str, str | int]:
    """手写 Reflection agent（写 → critic → 修订循环）。

    Args:
        generator_llm: 生成器 LLM。
        critic_llm: 批判器 LLM。
        task: 任务描述。
        max_iterations: 最大迭代次数。
        accept_marker: critic 表示满意的标记。

    Returns:
        包含 draft / critique / final / iteration 的 dict。
    """
    draft = ""
    critique = ""
    iteration = 0

    for iteration in range(1, max_iterations + 1):
        # Step 1: generator 生成/修订
        prompt = f"任务: {task}\n"
        if critique:
            prompt += f"之前的版本被批评: {critique}\n请改进。"
        gen_response = generator_llm.invoke([HumanMessage(content=prompt)])
        draft = str(gen_response.content)

        # Step 2: critic 批判
        crit_response = critic_llm.invoke(
            [HumanMessage(content=f"请评价以下内容,如果满意请说 {accept_marker}:\n\n{draft}")]
        )
        critique = str(crit_response.content)

        # Step 3: 检查是否满意
        if accept_marker in critique:
            return {"draft": draft, "critique": critique, "final": draft, "iteration": iteration}

    # 超过 max_iterations,返回最后一次 draft
    return {"draft": draft, "critique": critique, "final": draft, "iteration": iteration}
