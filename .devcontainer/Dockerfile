FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm

# 装 uv
COPY --from=ghcr.io/astral-sh/uv:0.5.0 /uv /uvx /usr/local/bin/

# 装常用工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    make \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 切换非 root 用户
USER vscode

WORKDIR /workspaces/AgentTask
