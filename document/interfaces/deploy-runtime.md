# Deploy And Runtime Interfaces（Predict）

> 最近更新：2026-04-29  
> 适用范围：`.streamlit/config.toml`、`deploy/deploy.sh`、`deploy/nginx_predict.conf`

## 当前运行时事实

- Streamlit 地址：`0.0.0.0:8501`
- `server.baseUrlPath = "predict"`
- 公开路径：`/predict`
- 建议服务器目录：`/opt/predict-webapp`
- 建议 systemd 服务名：`predict-webapp`
- 典型运行负载：上传后立即触发一步预测 + rolling 回测（可能持续数十秒）

## 核心文件与职责

| 文件 | 角色 |
|---|---|
| `.streamlit/config.toml` | Streamlit 地址、端口、`baseUrlPath`、上传大小 |
| `deploy/deploy.sh` | 服务器 bootstrap：依赖、venv、systemd、UFW、默认配置 |
| `deploy/nginx_predict.conf` | `/predict` 子路径反向代理模板 |

## `.streamlit/config.toml`

关键项：

```toml
[server]
address = "0.0.0.0"
port = 8501
headless = true
baseUrlPath = "predict"
maxUploadSize = 100
```

如果改公开子路径，必须同步检查：

- `app.py`
- `.streamlit/config.toml`
- `deploy/nginx_predict.conf`

## Nginx 子路径 contract：`deploy/nginx_predict.conf`

固定两段：

- `location = /predict`
  - 302 到 `/predict/`
- `location ^~ /predict/`
  - 反代到 `http://127.0.0.1:8501`
  - 保留前缀
  - 带 websocket upgrade 头
  - 建议放宽读超时，避免回测阶段被提前断开

## 远端 bootstrap：`deploy/deploy.sh`

主要步骤：

1. 安装系统依赖
2. 准备 `/opt/predict-webapp`
3. 创建 venv 并安装 `requirements.txt`
4. 创建并重启 `predict-webapp.service`
5. 开放 UFW `22/8501`

## 常用运维命令

```bash
systemctl restart predict-webapp
systemctl is-active predict-webapp
journalctl -u predict-webapp -n 50 --no-pager
```

## 修改规则

- 改公开路径：同步 `app.py`、`.streamlit/config.toml`、`deploy/nginx_predict.conf`
- 改服务名或目录：同步 `deploy/deploy.sh` 与本文档
- 改输入/输出协议（例如 `.xlsx` schema）：同步 `document/interfaces/frontend-contracts.md` 与 `document/interfaces/data-contract.md`
