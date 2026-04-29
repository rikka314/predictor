# AIE1902 Final — 时间序列预测 WebApp

## 在线访问

直接在浏览器打开：**https://gfm156.com/predictor**

上传 `.xlsx` 文件即可使用，无需本地安装。

---

## Windows 本地运行（一键启动）

### 前提条件

- 已安装 **Python 3.9+**（[下载地址](https://www.python.org/downloads/)，安装时务必勾选 **Add Python to PATH**）

### 启动步骤

1. 解压项目文件夹
2. **双击 `start.bat`**

脚本会自动完成以下操作：
- 检测 Python 环境
- 创建虚拟环境（首次运行）
- 安装所有依赖（首次运行，约 1-2 分钟）
- 启动 WebApp 并自动打开浏览器

首次启动约需 1-2 分钟（安装依赖），后续启动约 5 秒。

> 如浏览器未自动打开，请手动访问：**http://localhost:8501**

### 手动启动（可选）

```bash
cd final_test
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py --server.port 8501 --server.baseUrlPath ""
```

---

## 功能说明

1. **上传数据**：上传 `.xlsx` 文件（须含 `y` 列，可选 `date` 列）
2. **一步预测（Part 1）**：上传后自动输出下一期预测值 `ŷ_{N+1}`
3. **滚动回测（Part 2）**：按 80/20 时间切分，对测试段进行 rolling one-step 预测，展示：
   - 真实值 vs 预测值折线图
   - RMSE / MAE / MAPE 三项误差指标
4. **下载结果**：点击下载按钮获取回测预测结果 `.xlsx`

## 预测方法

集成模型（加权融合）：

| 模型 | 权重 | 说明 |
|------|------|------|
| Auto-ARIMA | 75% | 自动选阶的自回归模型 |
| XGBoost | 20% | 基于滞后特征的梯度提升树 |
| Holt-Winters (ETS) | 5% | 自动选择最优配置的指数平滑 |

## 输入文件要求

- 格式：`.xlsx`（Excel）
- 读取第一个 Sheet
- 必需列：`y`（数值，不可有缺失值）
- 可选列：`date`（用于时间轴显示和结果输出对齐）

## 输出文件格式

- 格式：`.xlsx`
- 包含列：`y`（预测值）；若输入有 `date`，输出也包含 `date`
- 行数 = 测试集长度（总行数 × 20%）

## 目录结构

```
final_test/
├── start.bat              ← Windows 一键启动
├── app.py                 ← 应用入口
├── requirements.txt       ← Python 依赖
├── dataset.xlsx           ← 示例数据
├── core/
│   ├── config.py          ← 配置常量
│   ├── io.py              ← 数据读写
│   └── predictor.py       ← 预测核心逻辑
├── ui/
│   ├── predict_page.py    ← 页面渲染
│   └── theme.py           ← 主题样式
├── .streamlit/
│   └── config.toml        ← Streamlit 配置
└── deploy/                ← 服务器部署脚本
```
