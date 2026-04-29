from __future__ import annotations

import streamlit as st


def inject_global_styles() -> None:
    st.markdown(
        """
        <style>
            .block-container {
                max-width: 1050px;
                padding-top: 1.5rem;
            }

            .stButton > button {
                border-radius: 10px;
            }

            /* metric card 样式增强 */
            [data-testid="stMetric"] {
                background: #fffdf8;
                border: 1px solid #e8e4dc;
                border-radius: 12px;
                padding: 0.8rem 1rem;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
            }

            [data-testid="stMetricLabel"] {
                font-size: 0.85rem;
                color: #6b7280;
            }

            [data-testid="stMetricValue"] {
                font-size: 1.35rem;
                font-weight: 600;
                color: #21303a;
            }

            /* 下载按钮样式 */
            .stDownloadButton > button {
                border-radius: 10px;
                background-color: #2f5d62;
                color: white;
                border: none;
                padding: 0.5rem 1.5rem;
                font-weight: 500;
                transition: background-color 0.2s;
            }

            .stDownloadButton > button:hover {
                background-color: #245149;
                color: white;
                border: none;
            }

            /* file uploader 区域 */
            [data-testid="stFileUploader"] {
                border-radius: 12px;
            }

            /* divider 轻量化 */
            hr {
                border: none;
                border-top: 1px solid #e8e4dc;
                margin: 1.2rem 0;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
