#!/usr/bin/env bash
set -euo pipefail

SERVER="predictor"
REMOTE_DIR="/opt/predictor"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"

for tool in ssh scp; do
  command -v "$tool" >/dev/null 2>&1 || { echo "[error] missing tool: $tool"; exit 1; }
done

for f in app.py requirements.txt .streamlit/config.toml deploy/nginx_predictor.conf; do
  [ -f "${PROJECT_DIR}/${f}" ] || { echo "[error] missing file: ${f}"; exit 1; }
done

echo "[sync] project: ${PROJECT_DIR}"
echo "[sync] server:  ${SERVER}"
echo "[sync] remote:  ${REMOTE_DIR}"
echo ""

ssh "${SERVER}" "mkdir -p ${REMOTE_DIR} ${REMOTE_DIR}/core ${REMOTE_DIR}/ui ${REMOTE_DIR}/.streamlit ${REMOTE_DIR}/deploy ${REMOTE_DIR}/data"

echo "[run] uploading app.py, requirements.txt ..."
scp "${PROJECT_DIR}/app.py" "${PROJECT_DIR}/requirements.txt" "${SERVER}:${REMOTE_DIR}/"

echo "[run] uploading core/ ..."
scp "${PROJECT_DIR}"/core/*.py "${SERVER}:${REMOTE_DIR}/core/"

echo "[run] uploading ui/ ..."
scp "${PROJECT_DIR}"/ui/*.py "${SERVER}:${REMOTE_DIR}/ui/"

echo "[run] uploading .streamlit/config.toml ..."
scp "${PROJECT_DIR}/.streamlit/config.toml" "${SERVER}:${REMOTE_DIR}/.streamlit/"

echo "[run] uploading deploy/ ..."
scp "${PROJECT_DIR}/deploy/deploy.sh" "${PROJECT_DIR}/deploy/nginx_predictor.conf" "${PROJECT_DIR}/deploy/sync.sh" "${SERVER}:${REMOTE_DIR}/deploy/"

echo "[run] restarting service ..."
ssh "${SERVER}" "systemctl restart predictor && sleep 2 && systemctl is-active predictor"

echo ""
echo "[done] sync complete"
echo "[done] app url: https://gfm156.com/predictor"
echo "[done] nginx template: ${REMOTE_DIR}/deploy/nginx_predictor.conf"
