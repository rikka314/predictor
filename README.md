# AIE1902 Final — 时间序列预测 WebApp

## 功能

- 上传 `.xlsx` 文件（含 `y` 列，可选 `date` 列）
- 自动生成一步预测（Part 1）
- 自动执行 80/20 滚动回测（Part 2）
- 下载回测预测结果 xlsx

## 预测方法

集成模型：Holt-Winters + Auto-ARIMA + XGBoost（加权融合）

## 目录结构

```text
final_test/
├── app.py
├── core/
│   ├── config.py
│   ├── io.py
│   └── predictor.py
├── ui/
│   ├── predict_page.py
│   └── theme.py
├── .streamlit/
│   └── config.toml
├── deploy/
│   ├── deploy.sh
│   └── nginx_predict.conf
└── requirements.txt
```

## 本地运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

访问：`http://localhost:8501/predict`

## 服务器部署

1. 上传项目到服务器（建议目录：`/opt/predict-webapp`）。
2. 执行：

```bash
chmod +x deploy/deploy.sh
sudo bash deploy/deploy.sh
```

3. 将 `deploy/nginx_predict.conf` 合并到 `gfm156.com` 的 Nginx 站点配置。
4. `nginx -t && systemctl reload nginx`

访问：`https://gfm156.com/predict`

最终访问：`https://gfm156.com/predict`

## 题目关键约束（来自 `promblem.md`）

- 输入：`.xlsx`，读取首个 sheet
- 必需列：`y`；可选列：`date`
- 上传后必须自动执行：
  - Part 1：一步预测 `y_{N+1}`
  - Part 2：80/20 时间切分 + rolling one-step 回测
- 输出：`.xlsx`，列为 `y`（必需）+ `date`（可选）
- 红线：禁止数据泄漏

## 当前状态说明

- 当前仓库已完成部署底座与文档框架。
- 业务代码仍是占位实现，尚未完全对齐最新题目输入输出协议。
- 本次已先完成框架与文档对齐，便于下一阶段按规范实施代码。

## 规范阅读顺序

- `AI_CONTEXT.md`
- `document/PROJECT_FRAMEWORK.md`
- `document/MODULE_INTERFACES.md`
- `document/FRONTEND_STYLE_STANDARD.md`
- `document/UI_DESIGN_GUIDE.md`
- `document/interfaces/frontend-contracts.md`
- `document/interfaces/data-contract.md`
- `document/interfaces/deploy-runtime.md`
