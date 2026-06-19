"""练习 1：定义 Event schema 并抽取。"""

from __future__ import annotations

from pydantic import BaseModel


class Event(BaseModel):
    """事件 schema。"""

    title: str
    date: str
    location: str


# TODO: 用 extract_with_schema 从文本抽取 Event
# text = "2026 年杭州 AI 大会将于 6 月 20 日在杭州国际会议中心举行"
# result = extract_with_schema(llm, text, Event)
