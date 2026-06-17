# 安全策略

## 报告漏洞

如果你发现了安全漏洞，**请不要在公开 issue 中讨论**。

请通过私下渠道联系仓库维护者：
- 在 GitHub 上发起 Private Vulnerability Report（推荐）
- 或邮件至维护者（如仓库 README 中列出）

我们会在 7 个工作日内回复，并与你协调修复时间表。

## 支持的版本

仅 `main` 分支 + 最新发布的 minor 版本接受安全更新。

## 密钥管理

本仓库严格禁止提交以下内容：
- API keys（DeepSeek / Anthropic / OpenAI / Tavily / LangSmith 等）
- 数据库密码
- `.env` 文件

`pre-commit` 配置了 `detect-secrets` 自动扫描；CI 也会做二次校验。如不慎提交，请立即旋转密钥，并通过 `git filter-repo` 清理历史。

## 工具调用与沙箱

`packages/sandbox/`（M4 阶段实现）提供 E2B + Docker 两种代码执行沙箱方案。生产场景下：
- 默认禁用 `python_repl` / `shell` 等高危工具
- 高危工具调用强制走 HITL 审批（`packages/agent_core/interrupt`）
- 沙箱默认无网络访问，需显式白名单
