"""5 个自定义工具：用于演示 function calling。"""

from __future__ import annotations

from tools import tool


@tool(name="add", description="把两个整数相加")
def add(a: int, b: int) -> int:
    return a + b


@tool(name="mul", description="把两个整数相乘")
def mul(a: int, b: int) -> int:
    return a * b


@tool(name="strlen", description="计算字符串长度")
def strlen(text: str) -> int:
    return len(text)


@tool(name="upper", description="将字符串转为大写")
def upper(text: str) -> str:
    return text.upper()


@tool(name="weather_mock", description="模拟天气查询（返回固定结果）")
def weather_mock(city: str) -> str:
    return f"{city}: 25°C, sunny"


ALL_CUSTOM_TOOLS = [add, mul, strlen, upper, weather_mock]
