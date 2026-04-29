# Module D — requirements.txt + deploy/ + README

## 负责范围
基础设施：依赖管理、部署配置

## 目标文件
- `requirements.txt`（完全替换）
- `deploy/deploy.sh`（更新）
- `deploy/nginx_predict.conf`（更新路径）
- `README.md`（更新说明）

---

## requirements.txt（完整替换内容）

```
streamlit>=1.32.0
pandas>=2.0.0
numpy>=1.24.0
openpyxl>=3.1.0
statsmodels>=0.14.0
pmdarima>=2.0.0
xgboost>=2.0.0
scikit-learn>=1.3.0
plotly>=5.18.0
```

---

## deploy/deploy.sh 关键更新

```bash
#!/usr/bin/env bash
set -euo pipefail

# 安装依赖
pip install -r requirements.txt

# 启动 streamlit（生产模式）
streamlit run app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.headless true \
  --browser.gatherUsageStats false
```

---

## deploy/nginx_predict.conf 关键配置

```nginx
location /predict/ {
    proxy_pass http://127.0.0.1:8501/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_read_timeout 120s;    # 回测可能需要较长时间
}

location /predict/_stcore/stream {
    proxy_pass http://127.0.0.1:8501/_stcore/stream;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

---

## README.md 关键内容

```markdown
# AIE1902 Final — 时间序列预测 WebApp

## 功能
- 上传 .xlsx 文件（含 `y` 列，可选 `date` 列）
- 自动生成一步预测（Part 1）
- 自动执行 80/20 滚动回测（Part 2）
- 下载回测预测结果 xlsx

## 预测方法
集成模型：Holt-Winters + Auto-ARIMA + XGBoost（加权融合）

## 本地运行
pip install -r requirements.txt
streamlit run app.py

## 部署
bash deploy/deploy.sh
```

---

## 本地安装验证命令

```bash
pip install -r requirements.txt
python -c "import statsmodels, pmdarima, xgboost, plotly, openpyxl; print('all ok')"
streamlit run app.py --server.headless true
```

## 注意事项
- pmdarima 首次安装可能需要编译，确保 gcc/clang 可用
- 云端部署（如 Streamlit Community Cloud）需在 `packages.txt` 中添加系统依赖（如有）
- 若部署平台内存 < 512MB，考虑 XGBoost n_estimators 降至 100
