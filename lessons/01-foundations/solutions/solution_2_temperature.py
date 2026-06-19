"""练习 2 答案：温度实验。"""

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
    return call_llm(llm, "请创意回答")
