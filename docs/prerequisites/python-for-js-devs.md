# Python for JS/TS Devs · 速查对照表

> 给数年前端经验、零 Python 基础的工程师。每条 Python 概念都映射到 JS/TS 的对应物，让你"用前端直觉学 Python"。
>
> 本文不求完整覆盖 Python 全部语法，只覆盖学习 Agent 开发**必需**的部分。需要更深入时再单独学。

## 0. 心智迁移：Python ↔ JS/TS 总图

| 维度 | JS/TS | Python |
|---|---|---|
| 包管理器 | `pnpm` / `npm` / `yarn` | **`uv`**（推荐）/ `pip` / `poetry` |
| 锁文件 | `pnpm-lock.yaml` | `uv.lock` |
| 项目清单 | `package.json` | `pyproject.toml` |
| 类型系统 | TypeScript | type hints + `mypy` |
| 类型校验时机 | 编译时（tsc） | 静态检查（mypy）；运行时不强制 |
| Schema 校验 | `zod` | `pydantic` |
| Lint + Format | `eslint` + `prettier` | `ruff`（一个工具搞定） |
| 测试 | `vitest` / `jest` | `pytest` |
| Async | `Promise` / `async/await` | `coroutine` / `async/await` |
| Hook 工具 | `husky` + `lint-staged` | `pre-commit` |
| 模块系统 | ESM `import` | `import` |
| 工作区 | pnpm workspace | uv workspace |
| Web 框架 | Express / Hono / Next API | FastAPI / Flask / Django |
| 运行时 | Node.js / Bun | CPython（标准 Python 解释器） |

## 1. 工具链：`uv` ≈ `pnpm`

### 安装 uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 常用命令对照

| 操作 | pnpm | uv |
|---|---|---|
| 装依赖 | `pnpm install` | `uv sync` |
| 加运行时依赖 | `pnpm add foo` | `uv add foo` |
| 加 dev 依赖 | `pnpm add -D foo` | `uv add --dev foo` |
| 删依赖 | `pnpm remove foo` | `uv remove foo` |
| 升级 | `pnpm update` | `uv lock --upgrade` |
| 跑脚本 | `pnpm run dev` | `uv run xxx` |
| 在虚拟环境跑 | (不需要) | `uv run python script.py` |
| 创建工作区 | `pnpm-workspace.yaml` | `[tool.uv.workspace]` in pyproject.toml |

**关键差异**：Python 默认全局共享解释器与依赖，因此每个项目需要"虚拟环境"（`.venv/`）。`uv` 会自动管理这个目录，你基本感知不到。`uv run` 等同于 `pnpm exec` + 自动激活虚拟环境。

## 2. 模块与导入

### JS/TS

```ts
import { foo, bar } from "./module";
import * as utils from "./utils";
import defaultExport from "./mod";
```

### Python

```python
from .module import foo, bar       # 相对导入
from package.module import foo     # 绝对导入
import package.utils as utils      # 整模块导入
# Python 没有 default export 概念
```

**关键差异**：
- Python 包靠目录里的 `__init__.py` 标识（现代 Python 3.3+ 也支持隐式命名空间包）。
- 相对导入用前导点：`.` = 同级，`..` = 上一级。
- 没有 `default export`——所有导出都是命名导出。

## 3. 类型系统：type hints ≈ TypeScript（但运行时不强制）

### JS/TS

```ts
function greet(name: string, age: number): string {
  return `${name} is ${age}`;
}

interface User {
  id: string;
  name: string;
  age?: number;
}
```

### Python

```python
def greet(name: str, age: int) -> str:
    return f"{name} is {age}"

# Python 没有 interface,但有等价物:
from typing import TypedDict

class User(TypedDict):
    id: str
    name: str
    age: int  # 必需
    # age: NotRequired[int]  # 可选,需要 from typing import NotRequired

# 或者用 dataclass / pydantic
from dataclasses import dataclass

@dataclass
class User:
    id: str
    name: str
    age: int | None = None
```

**关键差异**：
- Python type hint **不在运行时强制**。错的类型不会报错，除非你用 `pydantic` 做运行时校验。
- 用 `mypy` 做静态检查（≈ tsc）。
- 现代 Python（3.10+）支持 `int | None` 写法（≈ TypeScript 联合类型）。
- `Optional[int]` 等价于 `int | None`，但后者更现代。

### 常用类型对照

| TS | Python |
|---|---|
| `string` | `str` |
| `number` | `int` 或 `float`（区分整数与浮点） |
| `boolean` | `bool` |
| `null` | `None` |
| `undefined` | (没有) |
| `string[]` | `list[str]` |
| `Record<string, number>` | `dict[str, int]` |
| `[string, number]` | `tuple[str, int]` |
| `string \| number` | `str \| int` |
| `Promise<string>` | `Coroutine[..., str]` 或 `Awaitable[str]` |
| `void` 返回 | `-> None` |
| `any` | `Any`（来自 typing 模块） |
| `unknown` | `object` 或 `Any` |

## 4. Schema 校验：`pydantic` ≈ `zod`

### JS/TS（zod）

```ts
import { z } from "zod";

const UserSchema = z.object({
  id: z.string(),
  name: z.string().min(1),
  age: z.number().int().positive().optional(),
});

type User = z.infer<typeof UserSchema>;
const user = UserSchema.parse(input);  // 抛错或返回类型安全对象
```

### Python（pydantic v2）

```python
from pydantic import BaseModel, Field, ValidationError

class User(BaseModel):
    id: str
    name: str = Field(min_length=1)
    age: int | None = Field(default=None, gt=0)

# 验证
try:
    user = User.model_validate(input_dict)  # 抛 ValidationError 或返回 User 实例
except ValidationError as e:
    print(e.errors())

# JSON 解析
user = User.model_validate_json(json_str)

# 序列化
data = user.model_dump()       # → dict
json = user.model_dump_json()  # → str
```

**关键差异**：
- pydantic 是类继承形态，zod 是 builder 形态。
- pydantic 字段直接是类属性 + type hint + `Field(...)` 修饰。
- pydantic 不可变请用 `model_config = ConfigDict(frozen=True)`。

## 5. Async / Await ≈ JS Promise

### JS/TS

```ts
async function fetchUser(id: string): Promise<User> {
  const res = await fetch(`/api/users/${id}`);
  return await res.json();
}

const users = await Promise.all([fetchUser("1"), fetchUser("2")]);
```

### Python

```python
import asyncio
import httpx

async def fetch_user(user_id: str) -> dict:
    async with httpx.AsyncClient() as client:
        res = await client.get(f"/api/users/{user_id}")
        return res.json()

# 并行
users = await asyncio.gather(fetch_user("1"), fetch_user("2"))
```

**关键差异**：
- Python `async def` ≈ JS `async function`。
- `await` 用法一致。
- 并行：`asyncio.gather(...)` ≈ `Promise.all([...])`。
- Python 必须在 async 上下文里才能 `await`，顶层脚本要 `asyncio.run(main())`。
- Python 的 `with` ≈ JS 没有直接对应物，但 `async with` 类似 RAII（资源自动释放）。

## 6. 异常处理

### JS/TS

```ts
try {
  await doWork();
} catch (e) {
  if (e instanceof ValidationError) {
    // ...
  }
} finally {
  cleanup();
}
```

### Python

```python
try:
    await do_work()
except ValidationError as e:
    ...
except (NetworkError, TimeoutError) as e:  # 多种异常合并
    ...
except Exception as e:                       # 兜底
    ...
finally:
    cleanup()
```

## 7. 容器与解构

| TS | Python |
|---|---|
| `[1, 2, 3]` | `[1, 2, 3]`（list） |
| `{a: 1, b: 2}` | `{"a": 1, "b": 2}`（dict） |
| `new Set([1, 2])` | `{1, 2}`（set） |
| `[1, "a"]` 元组 | `(1, "a")`（tuple，不可变） |
| `const [a, b] = arr` | `a, b = arr` |
| `const {x, y} = obj` | (无内建解构，需手动 `obj["x"]`) 或 `match` |
| `arr.map(x => x * 2)` | `[x * 2 for x in arr]`（列表推导） |
| `arr.filter(x => x > 0)` | `[x for x in arr if x > 0]` |
| `arr.reduce(...)` | `functools.reduce(...)`（少用,常用循环） |

## 8. Class（与 JS Class 几乎一致）

```python
from dataclasses import dataclass

class Animal:
    def __init__(self, name: str) -> None:
        self.name = name              # 实例属性

    def speak(self) -> str:           # 方法（self ≈ this）
        return "..."

class Dog(Animal):
    def speak(self) -> str:
        return "Woof"

# 或者更简洁:
@dataclass
class Point:
    x: float
    y: float
    # 自动生成 __init__ / __repr__ / __eq__
```

**关键差异**：
- `self` 必须显式作为方法第一个参数。
- 没有 `private` / `public`，约定用下划线 `_foo` 表示"内部使用"。
- `@dataclass` 装饰器 ≈ TS 的 `interface`/`class`+`constructor` 自动生成。

## 9. 函数式工具

| 操作 | JS | Python |
|---|---|---|
| map | `arr.map(fn)` | `[fn(x) for x in arr]` 或 `map(fn, arr)` |
| filter | `arr.filter(fn)` | `[x for x in arr if fn(x)]` |
| zip | `arr1.map((a,i)=>[a,arr2[i]])` | `zip(arr1, arr2)` |
| 排序 | `arr.sort((a,b)=>a-b)` | `sorted(arr, key=lambda x: x)` |
| Lambda | `(x) => x * 2` | `lambda x: x * 2` |
| 解包 | `[...arr1, ...arr2]` | `[*arr1, *arr2]`，dict 用 `{**d1, **d2}` |

## 10. 装饰器（你已经在 Next.js 见过：`@`）

```python
def log(func):
    def wrapper(*args, **kwargs):
        print(f"calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@log
def add(a: int, b: int) -> int:
    return a + b
```

≈ TypeScript decorator（实验性），FastAPI/LangChain 大量用。本课程会用到 `@tool`、`@app.get(...)`、`@dataclass`、`@property` 等。

## 11. 上下文管理器（`with` 语句）

```python
# 文件
with open("file.txt") as f:
    data = f.read()
# 自动关闭文件,无需手动 close

# 异步
async with httpx.AsyncClient() as client:
    res = await client.get(url)
```

≈ Java try-with-resources / C# using。JS 没有直接对应物（`Symbol.dispose` 提案中）。

## 12. 测试：`pytest` ≈ `vitest`

```python
# tests/test_math.py
def test_add():
    assert add(2, 3) == 5

def test_add_negative():
    assert add(-1, 1) == 0

# Fixture（≈ vitest 的 beforeEach + 依赖注入）
import pytest

@pytest.fixture
def user():
    return User(id="1", name="Alice")

def test_user_name(user):
    assert user.name == "Alice"

# 异步测试
@pytest.mark.asyncio  # 如果用了 asyncio_mode = "auto" 可省略
async def test_async():
    result = await fetch_user("1")
    assert result["id"] == "1"

# 参数化（≈ vitest 的 test.each）
@pytest.mark.parametrize("a,b,expected", [(1,2,3), (0,0,0), (-1,1,0)])
def test_add_table(a, b, expected):
    assert add(a, b) == expected
```

## 13. f-string（模板字符串）

```python
name = "Alice"
age = 30

# JS: `hello ${name}, age ${age}`
# Python:
greeting = f"hello {name}, age {age}"

# 表达式
result = f"sum: {1 + 2}"            # "sum: 3"

# 调试输出（=）
debug = f"{name=}"                  # "name='Alice'"

# 格式化
pi = f"{3.14159:.2f}"               # "3.14"
```

## 14. Path 操作：`pathlib`

```python
from pathlib import Path

p = Path("docs") / "readme.md"      # ≈ path.join
p.exists()
p.read_text()
p.write_text("hello")
p.parent
p.suffix                            # ".md"
p.stem                              # "readme"

# 遍历
for f in Path("src").rglob("*.py"):
    print(f)
```

## 15. 调试

```python
# 最简: print
print(value)

# 类型 + 值（开发期超有用）
print(f"{value=}")

# 真正调试: pdb / ipdb
breakpoint()  # 程序停在这里,进入交互式调试

# IDE 断点（VS Code 自动支持）

# 日志
import structlog
log = structlog.get_logger()
log.info("event_happened", user_id=42, action="click")
```

## 16. 快速避坑清单

1. **缩进就是语法**：4 空格缩进，混用 tab/space 会报错。VS Code + ruff format 自动处理。
2. **可变默认参数陷阱**：`def f(x=[])` 共享同一个 list。请用 `def f(x: list | None = None)` 然后 `if x is None: x = []`。
3. **`is` ≠ `==`**：`is` 比较对象身份，`==` 比较值。比较 `None` 用 `is None`。
4. **`None` 不是 falsy 的全部**：`if x:` 在 `x = 0 / "" / [] / None` 时都为假。判断 None 请显式 `if x is None:`。
5. **`int / int = float`**：`5 / 2 == 2.5`。整除用 `5 // 2 == 2`。
6. **导入循环**：相对导入循环会立刻报错。打破方法：把共享代码提取到底层模块。
7. **没有 `const`**：约定用大写命名常量 `MAX_RETRIES = 3`，但仍然可被改。
8. **没有 `let` / `var`**：变量一律 `x = 1` 直接赋值。

## 17. 学完这个文档之后

你已经具备读懂 90% Agent 开发代码的语法基础。**剩下 10% 边学边查**——遇到不懂的再回来翻这份文档，或者在对应章节查具体用法。

下一步：进入 `lessons/01-foundations/`（M2 后上线）。

---

## 附：推荐资源（按需查阅，不必预读）

- 官方教程：https://docs.python.org/3/tutorial/
- pydantic v2 文档：https://docs.pydantic.dev/latest/
- ruff 规则：https://docs.astral.sh/ruff/rules/
- mypy 速查：https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html
- uv 文档：https://docs.astral.sh/uv/
