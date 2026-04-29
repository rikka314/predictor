# Module Interfaces Index（Predict）

> 最近更新：2026-04-29  
> 作用：模块边界总索引，详细契约统一下沉到 `document/interfaces/`

## 读取顺序

1. `AI_CONTEXT.md`
2. 本文档
3. 按任务跳转到对应契约文件

## 模块总览

| 模块 | 职责 | 详细文档 |
|---|---|---|
| 前端壳层与页面 | 上传、自动触发、结果展示、下载入口 | `document/interfaces/frontend-contracts.md` |
| 数据协议与评估规则 | 输入/输出 schema、评分指标、无泄漏约束 | `document/interfaces/data-contract.md` |
| 部署与运行时 | 子路径、服务、Nginx、运行约束 | `document/interfaces/deploy-runtime.md` |

## 变更同步规则

- 改页面输入输出：同步 `frontend-contracts.md` 与 `data-contract.md`
- 改数据协议：同步 `data-contract.md` 与 `AI_CONTEXT.md`
- 改部署路径或服务名：同步 `deploy-runtime.md` 与 `AI_CONTEXT.md`
