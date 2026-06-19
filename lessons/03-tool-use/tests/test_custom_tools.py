"""custom_tools 测试：5 个自定义工具验证。"""

from __future__ import annotations

import pytest

from tools import tool


@pytest.fixture(autouse=True)
def _clear_registry() -> None:
    from tools import registry as _reg

    _reg._REGISTRY.clear()


@pytest.mark.fast
def test_add_tool() -> None:
    @tool(name="add", description="加法")
    def add(a: int, b: int) -> int:
        return a + b

    assert add.run({"a": 1, "b": 2}) == 3


@pytest.mark.fast
def test_mul_tool() -> None:
    @tool(name="mul", description="乘法")
    def mul(a: int, b: int) -> int:
        return a * b

    assert mul.run({"a": 3, "b": 4}) == 12


@pytest.mark.fast
def test_strlen_tool() -> None:
    @tool(name="strlen", description="字符串长度")
    def strlen(text: str) -> int:
        return len(text)

    assert strlen.run({"text": "hello"}) == 5


@pytest.mark.fast
def test_upper_tool() -> None:
    @tool(name="upper", description="转大写")
    def upper(text: str) -> str:
        return text.upper()

    assert upper.run({"text": "hi"}) == "HI"


@pytest.mark.fast
def test_weather_mock_tool() -> None:
    @tool(name="weather_mock", description="模拟天气查询")
    def weather_mock(city: str) -> str:
        return f"{city}: 25°C, sunny"

    assert weather_mock.run({"city": "杭州"}) == "杭州: 25°C, sunny"
