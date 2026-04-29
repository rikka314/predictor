#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/predict-webapp"
SERVICE_NAME="predict-webapp"

echo "[1/6] 安装系统依赖..."
apt-get update -y
apt-get install -y python3 python3-pip python3-venv curl ufw

echo "[2/6] 准备目录..."
mkdir -p "${APP_DIR}"
mkdir -p "${APP_DIR}/data"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "${SCRIPT_DIR}")"

if [ -f "${PARENT_DIR}/app.py" ]; then
  echo "从 ${PARENT_DIR} 复制项目文件到 ${APP_DIR}"
  cp -f "${PARENT_DIR}/app.py" "${APP_DIR}/"
  cp -f "${PARENT_DIR}/requirements.txt" "${APP_DIR}/"
  mkdir -p "${APP_DIR}/core" "${APP_DIR}/ui" "${APP_DIR}/deploy" "${APP_DIR}/.streamlit"
  cp -rf "${PARENT_DIR}/core/"*.py "${APP_DIR}/core/" 2>/dev/null || true
  cp -rf "${PARENT_DIR}/ui/"*.py "${APP_DIR}/ui/" 2>/dev/null || true
  cp -rf "${PARENT_DIR}/deploy/"* "${APP_DIR}/deploy/" 2>/dev/null || true
  cp -f "${PARENT_DIR}/.streamlit/config.toml" "${APP_DIR}/.streamlit/config.toml"
else
  if [ ! -f "${APP_DIR}/app.py" ]; then
    echo "未找到 app.py，请先上传项目文件到 ${APP_DIR}"
    exit 1
  fi
fi

echo "[3/6] 创建虚拟环境并安装依赖..."
cd "${APP_DIR}"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "[4/6] 配置 systemd..."
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Predict WebApp (Streamlit)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${APP_DIR}
Environment="PATH=${APP_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=${APP_DIR}/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true --browser.gatherUsageStats=false
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ${SERVICE_NAME}.service
systemctl restart ${SERVICE_NAME}.service

echo "[5/6] 防火墙配置..."
ufw allow 22/tcp
ufw allow 8501/tcp
ufw --force enable

echo "[6/6] 完成"
PUBLIC_IP=$(curl -s --connect-timeout 5 http://ifconfig.me || echo "YOUR_SERVER_IP")
echo "临时访问地址: http://${PUBLIC_IP}:8501/predict"
echo "Nginx 子路径配置模板: ${APP_DIR}/deploy/nginx_predict.conf"
echo "将模板合并到 gfm156.com 的站点配置后，访问: https://gfm156.com/predict"
