# Project Conventions

> 最小化但能防住大部分问题的规范。不确定时参考现有代码。

## Python (collector)

| 项目 | 规则 |
|------|------|
| 行宽 | 88（ruff black 默认） |
| 引号 | 双引号（ruff format） |
| 导入 | 按 isort 分组：stdlib → third-party → local |
| 类型 | 使用 type hints；模块级用 `from __future__ import annotations` |
| 命名 | 变量/函数 snake_case；类 PascalCase；常量 UPPER_SNAKE_CASE |
| 文件 | 每个文件只做一件事；测试与源码同级 `tests/` 目录 |

## TypeScript/JS (web)

| 项目 | 规则 |
|------|------|
| 引号 | 双引号（biome） |
| 分号 | 有（biome） |
| 缩进 | 2 空格 |
| 类型 | 不隐式用 `any`；明确标注返回值类型 |
| 命名 | 变量/函数 camelCase；组件 PascalCase；常量 UPPER_SNAKE_CASE |
| 文件 | 组件放 `components/`；页面放 `app/`；工具函数放 `lib/` |

## Git 提交信息

格式：`type(scope): description`

| type | 含义 |
|------|------|
| `feat` | 新功能 |
| `fix` | bug 修复 |
| `refactor` | 重构（不改行为） |
| `chore` | 配置/工具/依赖 |
| `docs` | 文档 |
| `test` | 测试 |

示例：`feat(collector): add HN RSS source`

## 分支工作流

**所有修改走短命分支，禁止直接改 main。**

```powershell
git checkout main && git pull origin main
git checkout -b feature/<描述>
# 修改、提交
git push origin feature/<描述>
gh pr create --base main --head feature/<描述> --title "type: <标题>"
# 盯 CI → squash merge → 收尾
```

## 评审规则

**本项目运行在本地模型上，评审改为串行单代理执行：**

- 每次只做一项评审（代码标准 / 功能正确 / 安全性），不要并行
- 不使用子代理（sub-agent），当前代理独立完成
- 评审发现多个问题时，逐个列出并逐个修复
