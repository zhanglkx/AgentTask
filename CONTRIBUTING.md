# 贡献指南

感谢你考虑为 AgentTask 项目贡献代码。

本仓库的主要定位是教学项目，但同样欢迎社区贡献：修复 bug、改进文档、补充练习题、增加新章节示例。

## 开发环境

参见根 README 的"快速开始"。一条 `make setup` 即可完成全部环境准备。

## 提交流程

1. Fork 仓库 → 在自己仓库的 `main` 分支基础上拉特性分支：
   - `feat/xxx` 新功能
   - `fix/xxx` Bug 修复
   - `docs/xxx` 文档改动
   - `chore/xxx` 杂项
   - `lesson/0X-yyy` 章节内容
2. 提交前请确保：
   - `make lint` 通过
   - `make type` 通过
   - `make test` 通过
   - 改动 `packages/` 或 `apps/` 时请补充测试
3. Commit message 遵循 [Conventional Commits](https://www.conventionalcommits.org/)，描述使用中文：
   - `feat(agent_core): 添加 ReAct 模式 graph 模板`
   - `fix(retrieval): 修复 Qdrant 客户端连接超时`
   - `docs: 修正第 4 章 README 错别字`
4. 提交 PR 时请填写 PR 模板的 checklist。

## 章节贡献规范

新增 `lessons/` 章节时，目录结构需遵循：

```
lessons/0X-章节名/
├── README.md         # 中文讲解
├── notebook.ipynb    # 交互式探索（前期主导）
├── src/              # 可运行 .py 代码
├── tests/            # 配套测试
├── exercises/        # 练习题
├── solutions/        # 答案
└── NOTES.md          # 学习总结
```

## 行为准则

请遵守 [Contributor Covenant](https://www.contributor-covenant.org/) 行为准则。
