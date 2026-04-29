@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title 时间序列预测 WebApp

echo ============================================
echo   时间序列预测 WebApp - 一键启动
echo ============================================
echo.

REM --- 切换到脚本所在目录 ---
cd /d "%~dp0"

REM --- 检测 Python ---
set "PYTHON_CMD="

where python >nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=2 delims= " %%V in ('python --version 2^>^&1') do (
        echo %%V | findstr /R "^3\." >nul 2>&1
        if !errorlevel! equ 0 set "PYTHON_CMD=python"
    )
)

if not defined PYTHON_CMD (
    where python3 >nul 2>&1
    if !errorlevel! equ 0 set "PYTHON_CMD=python3"
)

if not defined PYTHON_CMD (
    where py >nul 2>&1
    if !errorlevel! equ 0 set "PYTHON_CMD=py -3"
)

if not defined PYTHON_CMD (
    echo [错误] 未检测到 Python 3
    echo        请先安装 Python 3.9 或更高版本
    echo        下载地址: https://www.python.org/downloads/
    echo        安装时请勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo [1/4] 检测到 Python:
!PYTHON_CMD! --version
echo.

REM --- 创建虚拟环境 ---
if not exist ".venv\Scripts\activate.bat" (
    echo [2/4] 正在创建虚拟环境 ...
    !PYTHON_CMD! -m venv .venv
    if !errorlevel! neq 0 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo       完成
) else (
    echo [2/4] 虚拟环境已存在，跳过创建
)
echo.

REM --- 激活虚拟环境 ---
call .venv\Scripts\activate.bat

REM --- 安装依赖 ---
echo [3/4] 正在检查并安装依赖 (首次约需 1-2 分钟) ...
pip install -r requirements.txt --quiet 2>nul
if !errorlevel! neq 0 (
    echo       尝试逐个安装 ...
    pip install streamlit pandas numpy openpyxl statsmodels pmdarima xgboost scikit-learn plotly --quiet 2>nul
)
echo       依赖安装完成
echo.

REM --- 启动应用 ---
echo [4/4] 正在启动 WebApp ...
echo.
echo ============================================
echo   应用即将在浏览器中自动打开
echo   如未自动打开，请手动访问:
echo.
echo     http://localhost:8501
echo.
echo   按 Ctrl+C 可停止应用
echo ============================================
echo.

streamlit run app.py --server.port 8501 --server.baseUrlPath "" --server.headless false --server.address localhost

if !errorlevel! neq 0 (
    echo.
    echo [错误] 应用启动失败，请检查上方错误信息
    pause
)

endlocal
