from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from sklearn.metrics import mean_absolute_error, mean_squared_error

from core.io import read_uploaded_xlsx, to_forecast_xlsx
from core.predictor import forecast_one_step, rolling_backtest


@st.cache_data(show_spinner=False)
def _run_one_step(series_tuple: tuple) -> float:
    return forecast_one_step(np.array(series_tuple))


@st.cache_data(show_spinner=False)
def _run_backtest(series_tuple: tuple) -> np.ndarray:
    return rolling_backtest(np.array(series_tuple))


def _build_backtest_chart(
    series: np.ndarray,
    bt_preds: np.ndarray,
    train_end: int,
    all_x: list | np.ndarray,
) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=all_x[:train_end],
            y=series[:train_end].tolist(),
            name="训练集",
            line=dict(color="#4C72B0"),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=all_x[train_end:],
            y=series[train_end:].tolist(),
            name="真实值",
            line=dict(color="#55A868"),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=all_x[train_end:],
            y=bt_preds.tolist(),
            name="预测值",
            line=dict(color="#C44E52", dash="dash"),
        )
    )

    fig.update_layout(
        title="滚动回测：真实值 vs 预测值",
        xaxis_title="时间",
        yaxis_title="y",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=20, t=60, b=40),
        hovermode="x unified",
    )
    return fig


def render_predict_page() -> None:
    uploaded = st.file_uploader("上传 Excel 文件 (.xlsx)", type=["xlsx"])

    if uploaded is None:
        st.info("请上传包含 `y` 列的 `.xlsx` 文件以开始预测。")
        return

    # --- 数据验证 ---
    try:
        df = read_uploaded_xlsx(uploaded.getvalue())
    except Exception as exc:
        st.error(f"读取文件失败：{exc}")
        return

    has_date = "date" in df.columns
    series = df["y"].to_numpy(dtype="float64")
    series_tuple = tuple(series)

    st.markdown("##### 数据预览")
    st.dataframe(df.head(20), use_container_width=True)

    st.divider()

    # --- Part 1: 一步预测 ---
    st.markdown("##### Part 1 · 一步预测")
    with st.spinner("正在计算一步预测..."):
        one_step_val = _run_one_step(series_tuple)
    st.metric("ŷ_{N+1}", f"{one_step_val:.6f}")

    st.divider()

    # --- Part 2: 滚动回测 ---
    st.markdown("##### Part 2 · 滚动回测")
    with st.spinner("正在进行回测，请稍候..."):
        bt_preds = _run_backtest(series_tuple)

    train_end = len(series) - len(bt_preds)
    actual = series[train_end:]

    # 折线图
    if has_date:
        dates = df["date"]
        all_x = dates.tolist()
    else:
        all_x = list(range(len(series)))

    fig = _build_backtest_chart(series, bt_preds, train_end, all_x)
    st.plotly_chart(fig, use_container_width=True)

    # 误差指标
    rmse = float(np.sqrt(mean_squared_error(actual, bt_preds)))
    mae = float(mean_absolute_error(actual, bt_preds))
    mape = float(np.mean(np.abs((actual - bt_preds) / (np.abs(actual) + 1e-8))) * 100)

    col1, col2, col3 = st.columns(3)
    col1.metric("RMSE", f"{rmse:.6f}")
    col2.metric("MAE", f"{mae:.6f}")
    col3.metric("MAPE", f"{mape:.2f}%")

    st.divider()

    # --- 下载 ---
    dates_test = df["date"].iloc[train_end:].reset_index(drop=True) if has_date else None
    xlsx_bytes = to_forecast_xlsx(bt_preds, dates=dates_test)

    st.download_button(
        label="⬇ 下载回测预测结果 (.xlsx)",
        data=xlsx_bytes,
        file_name="backtest_forecasts.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
