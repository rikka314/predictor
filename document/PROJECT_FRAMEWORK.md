# Project Framework（题目对齐版）

> 最近更新：2026-04-29  
> 说明：仅定义框架与职责，不包含具体实现代码

## 1) 目标框架

```text
final_test/
├── app.py                        # 页面入口（/predict）
├── core/
│   ├── config.py                 # 全局常量（train_ratio 等）
│   ├── io.py                     # xlsx 读取/校验/写出
│   └── predictor.py              # one-step 与 rolling 回测
├── ui/
│   ├── predict_page.py           # 上传即触发的主流程
│   └── theme.py                  # 全局样式入口
├── deploy/
│   ├── deploy.sh                 # 服务器部署
│   └── nginx_predict.conf        # /predict 反代模板
├── document/
│   ├── MODULE_INTERFACES.md
│   ├── PROJECT_FRAMEWORK.md
│   ├── FRONTEND_STYLE_STANDARD.md
│   ├── UI_DESIGN_GUIDE.md
│   └── interfaces/
│       ├── frontend-contracts.md
│       ├── data-contract.md
│       └── deploy-runtime.md
├── plan/                         # 后续实施计划
├── dataset.xlsx                  # 题目样例
├── promblem.md                   # 题目说明
└── README.md
```

## 2) 模块职责边界

- `core/io.py`：输入输出协议守门员（schema 校验 + 输出格式）
- `core/predictor.py`：预测计算引擎（禁止未来信息）
- `ui/predict_page.py`：题目流程编排（上传即算、结果展示、下载）
- `deploy/*`：部署与运行时保障（子路径可访问）
- `document/interfaces/*`：契约单一事实来源

## 3) 题目驱动的非功能约束

- 自动化：上传后自动开始计算
- 正确性：rolling 过程严格无泄漏
- 可用性：输出文件可直接用于评分验证
- 可部署性：`gfm156.com/predict` 稳定访问
