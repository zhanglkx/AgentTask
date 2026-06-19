"""练习 1 答案：定义 Event schema 并抽取。"""

from __future__ import annotations

from langchain_community.chat_models.fake import FakeListChatModel
from pydantic import BaseModel

from structured_extractor import extract_with_schema


class Event(BaseModel):
    """事件 schema。"""

    title: str
    date: str
    location: str


llm = FakeListChatModel(
    responses=['{"title": "杭州 AI 大会", "date": "2026-06-20", "location": "杭州国际会议中心"}'],
)

text = "2026 年杭州 AI 大会将于 6 月 20 日在杭州国际会议中心举行"
result = extract_with_schema(llm, text, Event)
print(result)
