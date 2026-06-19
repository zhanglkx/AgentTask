"""Coding agent 雏形：写 → 跑测试 → 修订。

类比前端:
    - Actor ≈ Feature developer（写代码）
    - Critic ≈ CI + code reviewer（跑测试 + 指出问题）
    - SUCCESS marker ≈ CI passing（"可以合并了"）

核心思路:
    与 writing_agent 类似,但 critic 用"跑测试"替代纯文本评价。
    在这个雏形版中,critic 仍然用 LLM 模拟"测试结果"——
    真实版会在 M4/M5 中接入 sandbox 来真正跑测试。

对比 agent_core.build_reflexion_graph + InMemoryExperienceStore:
    Reflexion 在 Reflection 基础上加经验记忆——从过去的成功/失败中学习。
"""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage


def run_coding_agent(
    actor_llm: BaseChatModel,
    critic_llm: BaseChatModel,
    task: str,
    *,
    max_iterations: int = 3,
    success_marker: str = "SUCCESS",
) -> dict[str, str | int]:
    """手写 Reflexion coding agent（写 → 测试 → 修订循环）。

    Args:
        actor_llm: 写代码的 LLM。
        critic_llm: 评价测试结果的 LLM。
        task: 任务描述。
        max_iterations: 最大迭代次数。
        success_marker: critic 表示成功的标记。

    Returns:
        包含 attempt / critique / iteration 的 dict。
    """
    attempt = ""
    critique = ""
    iteration = 0

    for iteration in range(1, max_iterations + 1):
        # Step 1: actor 写代码
        prompt = f"任务: {task}\n"
        if critique:
            prompt += f"之前的版本失败: {critique}\n请修复并重写。"
        actor_response = actor_llm.invoke([HumanMessage(content=prompt)])
        attempt = str(actor_response.content)

        # Step 2: critic 评价（模拟"跑测试"）
        crit_response = critic_llm.invoke(
            [HumanMessage(content=f"评价以下代码,如果测试通过请说 {success_marker}:\n\n{attempt}")]
        )
        critique = str(crit_response.content)

        # Step 3: 检查是否成功
        if success_marker in critique:
            return {"attempt": attempt, "critique": critique, "iteration": iteration}

    return {"attempt": attempt, "critique": critique, "iteration": iteration}
