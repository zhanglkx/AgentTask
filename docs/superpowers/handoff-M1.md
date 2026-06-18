# M1 实施交接 prompt

把下面整段（三道横线之间的内容）贴给接手的模型。

---

请接手执行一个进行中的 Python 项目实施计划。

## 项目位置
/Users/temptrip/Documents/GitHub/AgentTask
（这是一个 uv workspace；Python 3.12；非 git 远程，本地 git 仓库）

## 计划文件
docs/superpowers/plans/2026-06-17-M1-common-llm-providers.md
共 14 个 task，每个 task 含完整 TDD 步骤、可直接复制的代码、明确的 commit 消息。

## 当前进度（截至最后一次 commit）
- 分支：feat/m1-common-llm-providers
- HEAD：744a22b
- Task 1–8 已完成（packages/common 全部 6 个模块 + packages/llm_providers 骨架）
- packages/common 覆盖率 96%，43 测试通过
- 剩余：Task 9（4 个 provider builder）→ Task 14（覆盖率 gate + 收尾）

## 必须遵守的约定（之前踩过的坑）
1. **TDD**：测试先写，跑一次确认失败，再写实现，再跑确认通过，再 commit。每个 task 一个 commit。
2. **commit 消息**：Conventional Commits + 中文描述。完全照计划里给定的字符串，不要自己改写。commitizen pre-commit hook 会拦截不符合的格式。
3. **预提交钩子**：ruff / ruff-format / mypy / pytest-fast / detect-secrets / commitizen 都会在 commit 时跑。如果 mypy 因为新依赖报缺类型，把对应包加到 .pre-commit-config.yaml 的 mypy hook 的 additional_dependencies（已有先例：pydantic-settings、structlog、tenacity、redis、fakeredis）。
4. **不要跳过钩子**：禁用 --no-verify。如果钩子修了文件（end-of-file-fixer / ruff-format），重新 git add 再 commit。
5. **detect-secrets 假阳性**：在那一行加 `# pragma: allowlist secret` 注释。
6. **uv sync**：当 packages 之间互相依赖时，可能要用 `uv sync --all-packages` 才会装上 workspace 成员。
7. **ruff RUF001/002/003 已全局忽略**（中文标点）。RUF001 在 ruff.toml 已 ignore。
8. **测试 marker**：fast / integration / llm / slow 已注册；单元测试用 @pytest.mark.fast。
9. **conftest.py**：每个 packages/*/tests/conftest.py 必须有 autouse fixture 清掉 AGENTTASK_ 前缀环境变量，避免 .env 干扰单元测试。

## 一个待决策的偏差
Task 8 实施时，subagent 没创建 `packages/llm_providers/tests/__init__.py`，原因是和 `packages/common/tests/__init__.py` 同时存在会让 pytest 报 ImportPathMismatchError。它的建议是两个都删（pytest 用 testpaths 发现，不需要 __init__）。请你接手时先决定：
   - A) 删掉 packages/common/tests/__init__.py 保持一致（推荐）
   - B) 在两个 tests 目录都加 __init__.py 并用 pytest --import-mode=importlib

我倾向 A，干净。

## 工作流程（如果你是另一个 Claude Code）
按 superpowers:subagent-driven-development 跑：每个 task 派一个新的 general-purpose subagent，给它完整 task 文本（不要让它自己读 plan 文件，直接把 task 章节贴进 prompt）+ 上下文 + commit hash。subagent 完成后，主控制器读 git log 验证 commit 消息和文件变更，跑 pytest + ruff + mypy 独立验证，再进入下一个 task。

## 工作流程（如果你不是 Claude Code 或不用 subagent）
顺序执行 Task 9 → 14。每个 task：
1. Read 计划里对应 task 的全部代码块
2. 用 Write 创建文件（注意 TDD 顺序：先测试再实现）
3. Bash 跑 pytest 确认通过
4. Bash 跑 `uv run ruff check packages/<pkg>` 和 `uv run mypy packages/<pkg>`
5. git add + git commit，commit 消息照计划写
6. 进入下一个 task

## 验收标准（M1 终点）
- examples/m1_provider_switch.py：5 行代码切换 DeepSeek↔Ollama
- 自动 cost 追踪 + 自动限流重试
- 覆盖率 ≥ 80%（pytest --cov-fail-under=80 配置）
- make lint / make type / make test 全绿

## 第一步建议
1. cd /Users/temptrip/Documents/GitHub/AgentTask
2. git status 确认在 feat/m1-common-llm-providers 分支
3. git log --oneline -10 看清楚已有 commit
4. 决定上面的 tests/__init__.py 偏差走 A 还是 B
5. 读 plan 文件 Task 9 章节（从 "## Task 9：" 开始，到 "## Task 10：" 之前）
6. 开干

不确定的事情停下来问，不要瞎猜。

---

## 给原作者（你自己）的备忘

- 这份交接文档对应 commit `744a22b` 时的状态。如果你之后又跑了几个 task 再切换模型，把"当前进度"那一节的 HEAD 哈希和已完成 task 范围更新一下再发出去。
- 如果接手方是没有 git 历史访问的纯文本环境（比如 ChatGPT 网页版），把 `git log --oneline -10` 的输出也粘进 prompt 里，省得对方瞎猜。
- M1 完成后，M2/M3/M4/M5/M6 各自需要单独的 plan + handoff，参考这份文档结构即可。
