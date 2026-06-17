"""初始化 Postgres schema 的入口脚本。

M0 阶段为占位实现:
- 校验 Postgres 可连通
- 不创建任何表（schema 由 M3 里程碑的 packages/agent_core/checkpointer 引入）

后续里程碑实际创建的 schema 包括:
- M3: langgraph checkpointer 表（messages / checkpoints / writes）
- M3: long-term memory 表（user_profiles / collections / episodes）
- M5: capstone 业务表（research_sessions / outlines / reports）
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    """入口函数。返回 exit code。"""
    print("[init_db] M0 阶段占位脚本,后续里程碑实际填充 schema。")

    # 简单提示当前环境配置（不连接,避免在 CI 等环境失败）
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "agenttask")
    print(f"[init_db] 期望 Postgres 在 {host}:{port}/{db}（实际连接由后续里程碑实现）")

    repo_root = Path(__file__).resolve().parent.parent
    print(f"[init_db] 仓库根目录: {repo_root}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
