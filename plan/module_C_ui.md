# Module C — ui/predict_page.py + ui/theme.py + app.py

## 负责范围
前端展示：上传、自动触发预测、可视化、下载

## 目标文件
- `ui/predict_page.py`
- `ui/theme.py`
- `app.py`

## UI 流程（严格按评分要求）

```
用户上传 xlsx
    ↓ 自动（无按钮）
[1] 数据验证（io.read_uploaded_xlsx）
    → 失败：st.error 显示原因，停止
    → 成功：显示数据预览（前 20 行）
    ↓
[2] Part 1：一步预测（displayed immediately）
    with st.spinner("正在计算一步预测..."):
        val = forecast_one_step(series)
    st.metric("一步预测 ŷ_{N+1}", f"{val:.6f}")
    ↓
[3] Part 2：滚动回测
    with st.spinner("正在进行回测，请稍候..."):
        bt_preds = rolling_backtest(series)
    显示：
      - 折线图（历史 + 回测预测 vs 真实值）
      - 误差指标卡片（RMSE / MAE / MAPE）
    ↓
[4] 下载按钮
    xlsx_bytes = to_forecast_xlsx(bt_preds, dates)
    st.download_button("下载回测预测结果 (.xlsx)", ...)
```

## 关键实现细节

### 自动触发（无按钮）
```python
# predict_page.py 中：
uploaded = st.file_uploader("上传 Excel 文件 (.xlsx)", type=["xlsx"])
if uploaded is not None:
    # 直接执行，不需要 st.button
    ...
```

### st.cache_data 缓存（避免重复计算）
```python
@st.cache_data(show_spinner=False)
def _run_backtest(series_tuple: tuple) -> np.ndarray:
    return rolling_backtest(np.array(series_tuple))

@st.cache_data(show_spinner=False)
def _run_one_step(series_tuple: tuple) -> float:
    return forecast_one_step(np.array(series_tuple))
```
注意：series 转为 tuple 作为 cache key。

### 折线图（用 plotly）
```python
import plotly.graph_objects as go

fig = go.Figure()
# 全量历史
fig.add_trace(go.Scatter(x=all_dates[:train_end], y=series[:train_end],
                         name="训练集", line=dict(color="#4C72B0")))
# 测试集真实值
fig.add_trace(go.Scatter(x=all_dates[train_end:], y=series[train_end:],
                         name="真实值", line=dict(color="#55A868")))
# 回测预测
fig.add_trace(go.Scatter(x=all_dates[train_end:], y=bt_preds,
                         name="预测值", line=dict(color="#C44E52", dash="dash")))
st.plotly_chart(fig, use_container_width=True)
```

### 误差指标
```python
from sklearn.metrics import mean_squared_error, mean_absolute_error
import numpy as np

actual = series[train_end:]
rmse = np.sqrt(mean_squared_error(actual, bt_preds))
mae  = mean_absolute_error(actual, bt_preds)
mape = np.mean(np.abs((actual - bt_preds) / (np.abs(actual) + 1e-8))) * 100

col1, col2, col3 = st.columns(3)
col1.metric("RMSE", f"{rmse:.6f}")
col2.metric("MAE",  f"{mae:.6f}")
col3.metric("MAPE", f"{mape:.2f}%")
```

### 下载 xlsx
```python
xlsx_bytes = to_forecast_xlsx(bt_preds, dates=dates_test if has_date else None)
st.download_button(
    label="⬇ 下载回测预测结果 (.xlsx)",
    data=xlsx_bytes,
    file_name="backtest_forecasts.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
```

## app.py 修改
```python
st.set_page_config(
    page_title="时间序列预测 WebApp",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)
```

## theme.py 修改
保持原有 CSS，可视情况增加 metric card 样式。

## 依赖
```
streamlit>=1.32.0
plotly>=5.18.0
scikit-learn>=1.3.0
```

## 测试要点
- 上传后立即触发（不点任何按钮）
- Part 1 显示单一数值
- Part 2 显示折线图 + 3 个指标
- 下载 xlsx 格式正确（openpyxl 可读，列为 y / date+y）
- 多次上传不同文件，cache 正确失效（tuple key 不同）
