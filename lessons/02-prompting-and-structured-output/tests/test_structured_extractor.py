"""structured_extractor 测试：Pydantic 结构化抽取。"""

from __future__ import annotations

import pytest
from langchain_community.chat_models.fake import FakeListChatModel
from pydantic import BaseModel

from structured_extractor import extract_with_schema


class Person(BaseModel):
    """人物信息 schema。"""

    name: str
    age: int
    occupation: str


class Company(BaseModel):
    """公司信息 schema。"""

    name: str
    founded: int
    industry: str


@pytest.mark.fast
def test_extract_person() -> None:
    """从文本抽取 Person 结构化信息。"""
    llm = FakeListChatModel(
        responses=[
            '{"name": "张三", "age": 30, "occupation": "工程师"}',
        ]
    )
    result = extract_with_schema(
        llm=llm,
        text="张三，30岁，是一名软件工程师。",
        schema=Person,
    )
    assert result.name == "张三"
    assert result.age == 30
    assert result.occupation == "工程师"


@pytest.mark.fast
def test_extract_company() -> None:
    """从文本抽取 Company 结构化信息。"""
    llm = FakeListChatModel(
        responses=[
            '{"name": "OpenAI", "founded": 2015, "industry": "AI"}',
        ]
    )
    result = extract_with_schema(
        llm=llm,
        text="OpenAI 成立于 2015 年，从事 AI 研究。",
        schema=Company,
    )
    assert result.name == "OpenAI"
    assert result.founded == 2015


@pytest.mark.fast
def test_extract_with_schema_returns_pydantic_object() -> None:
    """返回值应为 Pydantic BaseModel 实例。"""
    llm = FakeListChatModel(responses=['{"name": "A", "age": 1, "occupation": "B"}'])
    result = extract_with_schema(llm=llm, text="A 1 B", schema=Person)
    assert isinstance(result, BaseModel)
