# AI 快速上下文（Predict 底座）

> 最近更新：2026-04-29  
> 用途：项目级路由文档。先读本文件，再按任务跳到对应规范文档。  
> 约定：详细规范统一维护在 `document/`，本文件只保存 durable project facts。

## 项目一句话

这是一个基于 Streamlit 的时间序列预测 WebApp，面向课程 final 题目：用户上传 `.xlsx`（首个 sheet，必含 `y`，可选 `date`），系统自动完成一步预测与滚动回测，并导出规范化预测结果文件；线上通过 `gfm156.com/predictor` 对外提供服务。

## 关键运行事实

- 公开路径：`/predictor`
- Streamlit 配置：`server.baseUrlPath = "predictor"`
- 默认监听：`0.0.0.0:8501`
- 建议服务器目录：`/opt/predict-webapp`
- 建议 systemd 服务名：`predict-webapp`
- Nginx 子路径模板：`deploy/nginx_predict.conf`
- 一键部署脚本：`deploy/deploy.sh`

## 题目约束快照（以 `promblem.md` 为准）

- 输入文件：`.xlsx`，只读取第一个 sheet。
- 输入列：必需 `y`（数值、不可缺失）；可选 `date`（仅用于显示与输出对齐）。
- Part 1：上传后立即输出单个一步预测 `y_{N+1}`（不可让用户先选方法）。
- Part 2：按时间顺序 80/20 切分，测试段做严格 rolling one-step 预测。
- 输出文件：`.xlsx`，必须含单列 `y`（预测值）；若输入有 `date`，输出也携带 `date`。
- 红线：严禁数据泄漏（预测时不可使用未来值）。

## 已知样例数据（`dataset.xlsx`）

- 首 sheet：`Sheet1`
- 列结构：`date`, `y`
- 记录量：约 500 行样本（含表头共 501 行）
- 用途：用于本地联调，不应当硬编码到算法逻辑中

## 仓库地图

- `app.py`
  - 作用：WebApp 入口与页面壳层。
- `core/`
  - 作用：数据读取、预测逻辑、配置常量。
- `ui/`
  - 作用：页面渲染与共享主题。
- `deploy/`
  - 作用：部署脚本与 Nginx 子路径模板。
- `document/`
  - 作用：前端风格、UI 指南、接口与运行时契约。
- `plan/`
  - 作用：按题目约束拆分的实施计划与模块任务。

## 当前冻结模块边界

- 页面入口：`app.py`
- 预测页：`ui/predict_page.py`
- 共享主题：`ui/theme.py`
- 数据读取：`core/io.py`
- 预测主逻辑：`core/predictor.py`

## 默认阅读路线

| 任务类型 | 优先阅读 |
|---|---|
| 快速定位模块边界 | `document/MODULE_INTERFACES.md` |
| UI 调整、页面视觉统一 | `document/FRONTEND_STYLE_STANDARD.md` + `document/UI_DESIGN_GUIDE.md` |
| 页面输入输出与组件边界 | `document/interfaces/frontend-contracts.md` |
| 数据输入/输出与评估指标约束 | `document/interfaces/data-contract.md` |
| 部署、子路径、Nginx、服务运行 | `document/interfaces/deploy-runtime.md` |

## 协作约定

- 项目级 Skill：`.cursor/skills/predict-workspace-context/SKILL.md`，进入本工作区处理代码/文档/UI/部署任务时先使用它读取本文件。
- `AI_CONTEXT.md` 只保存稳定事实，不堆放细节实现。
- 详细规范优先沉淀到 `document/` 与 `document/interfaces/`。
- 新增页面或部署变更时，先改代码，再回写本文件与对应契约文档。
- 如本次工作改动 durable facts，结束时同步更新本文件。
