"""练习 2：温度实验（用 FakeListChatModel 模拟）。

任务:
1. 用 call_llm 调 FakeListChatModel，观察相同输入在不同 responses 下的输出
2. 理解 temperature 的作用：0 = 确定性（总是第一个 response），>0 = 随机选择

提示:
- FakeListChatModel 没有真正的 temperature 参数，但可以通过 responses 列表模拟多样性
"""

from __future__ import annotations

from langchain_community.chat_models.fake import FakeListChatModel

from hello_llm import call_llm


def exercise_2_deterministic() -> str:
    """temperature=0 时应确定性输出。"""
    llm = FakeListChatModel(responses=["确定答案"])
    return call_llm(llm, "问题")


def exercise_2_creative() -> str:
    """高 temperature 时可能有多个不同回答（模拟）。"""
    llm = FakeListChatModel(responses=["创意答案A", "创意答案B", "创意答案C"])
    # FakeListChatModel 会按顺序返回 responses
    return call_llm(llm, "请创意回答")
