"""结构化抽取：用 Pydantic schema 让 LLM 输出结构化数据。

类比前端:
    - Pydantic BaseModel ≈ Zod schema / TypeScript interface
    - model_validate_json() ≈ Zod.parse()
    - JSON schema ≈ OpenAPI spec

核心思路:
    LLM 不是返回纯文本，而是返回符合 schema 的 JSON 对象。
    Pydantic 自动将 JSON → Python 对象，就像 Zod 将 JSON → TS object。

    第一步：手写 parse（看清底层）—— FakeListChatModel 返回 JSON 字符串，
    用 Pydantic 的 model_validate_json() 解析。

    第二步（notebook 演示）：with_structured_output() 自动完成上述步骤。
"""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel


def extract_with_schema(
    llm: BaseChatModel,
    text: str,
    schema: type[BaseModel],
) -> BaseModel:
    """从文本中抽取符合 schema 的结构化信息（手写 JSON parse 版）。

    Args:
        llm: 任意 LangChain BaseChatModel。
        text: 要抽取的文本。
        schema: Pydantic BaseModel 类（定义输出结构）。

    Returns:
        schema 的 Pydantic 实例。
    """
    prompt = f"从以下文本中抽取信息，仅返回 JSON（不要其他文字）:\n\n{text}"
    response = llm.invoke(prompt)
    content = str(response.content)
    # LLM 可能返回带 markdown 代码块的 JSON，需清理
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    return schema.model_validate_json(cleaned)


def extract_with_structured_output(
    llm: BaseChatModel,
    text: str,
    schema: type[BaseModel],
) -> BaseModel:
    """用 with_structured_output() 自动结构化抽取（需支持 tool calling 的模型）。

    Args:
        llm: 需支持 with_structured_output 的 BaseChatModel。
        text: 要抽取的文本。
        schema: Pydantic BaseModel 类。

    Returns:
        schema 的 Pydantic 实例。
    """
    structured_llm = llm.with_structured_output(schema)
    prompt = f"从以下文本中抽取信息:\n\n{text}"
    return structured_llm.invoke(prompt)
