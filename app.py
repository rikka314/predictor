from __future__ import annotations

import streamlit as st

from ui.predict_page import render_predict_page
from ui.theme import inject_global_styles


st.set_page_config(
    page_title="时间序列预测 WebApp",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_global_styles()

st.title("时间序列预测 WebApp")
st.caption("上传 `.xlsx` 文件，自动完成一步预测与滚动回测")

render_predict_page()
