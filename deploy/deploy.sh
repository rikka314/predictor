#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/predictor"
SERVICE_NAME="predictor"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  时间序列预测 WebApp - 服务器部署脚本${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

echo -e "${YELLOW}[1/6] 安装系统依赖...${NC}"
apt-get update -y
apt-get install -y python3 python3-pip python3-venv curl ufw

echo -e "${GREEN}✓ 系统依赖安装完成${NC}"

echo -e "${YELLOW}[2/6] 准备目录...${NC}"
mkdir -p "${APP_DIR}"
mkdir -p "${APP_DIR}/data"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "${SCRIPT_DIR}")"
APP_REAL_DIR="$(readlink -f "${APP_DIR}")"
PARENT_REAL_DIR="$(readlink -f "${PARENT_DIR}")"

if [ -f "${PARENT_DIR}/app.py" ] && [ "${PARENT_REAL_DIR}" != "${APP_REAL_DIR}" ]; then
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
    echo -e "${RED}✗ 未找到 app.py，请先上传项目文件到 ${APP_DIR}${NC}"
    exit 1
  fi
fi

echo -e "${GREEN}✓ 项目目录准备完成: ${APP_DIR}${NC}"

echo -e "${YELLOW}[3/6] 创建虚拟环境并安装依赖...${NC}"
cd "${APP_DIR}"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}✓ Python 依赖安装完成${NC}"

echo -e "${YELLOW}[4/6] 创建 Streamlit 配置...${NC}"
mkdir -p "${APP_DIR}/.streamlit"

cat > "${APP_DIR}/.streamlit/config.toml" << 'EOF'
[server]
address = "0.0.0.0"
port = 8503
headless = true
baseUrlPath = "predictor"
maxUploadSize = 100

[browser]
gatherUsageStats = false
EOF

echo -e "${GREEN}✓ Streamlit 配置完成${NC}"

echo -e "${YELLOW}[5/6] 配置 systemd 服务...${NC}"

cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=时间序列预测 WebApp (Streamlit)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${APP_DIR}
Environment="PATH=${APP_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=${APP_DIR}/venv/bin/streamlit run app.py --server.port=8503 --server.address=0.0.0.0 --server.headless=true --browser.gatherUsageStats=false
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ${SERVICE_NAME}.service
systemctl restart ${SERVICE_NAME}.service

echo -e "${GREEN}✓ systemd 服务配置完成${NC}"

echo -e "${YELLOW}[6/6] 防火墙配置...${NC}"
ufw allow 22/tcp
ufw allow 8503/tcp
ufw --force enable

echo -e "${GREEN}✓ 防火墙配置完成${NC}"

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}  ✅ 部署完成！${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

PUBLIC_IP=$(curl -s --connect-timeout 5 http://ifconfig.me 2>/dev/null || echo "115.191.68.122")

echo -e "  📊 临时访问地址: ${GREEN}http://${PUBLIC_IP}:8503/predictor${NC}"
echo -e "  Nginx 子路径模板: ${YELLOW}${APP_DIR}/deploy/nginx_predictor.conf${NC}"
echo ""
echo -e "  常用命令:"
echo -e "    查看状态:  ${YELLOW}systemctl status ${SERVICE_NAME}${NC}"
echo -e "    查看日志:  ${YELLOW}journalctl -u ${SERVICE_NAME} -f${NC}"
echo -e "    重启服务:  ${YELLOW}systemctl restart ${SERVICE_NAME}${NC}"
echo -e "    停止服务:  ${YELLOW}systemctl stop ${SERVICE_NAME}${NC}"
echo ""
echo -e "${RED}  ⚠️ 重要提醒：${NC}"
echo -e "  请确保在火山引擎控制台的 ${YELLOW}安全组${NC} 中放通 ${YELLOW}8503${NC} 端口！"
echo -e "  如需接入 gfm156.com/predictor，请把 deploy/nginx_predictor.conf 合并到站点 Nginx 配置后再 reload nginx"
echo ""
