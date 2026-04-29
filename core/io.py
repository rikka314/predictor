from __future__ import annotations

from io import BytesIO

import numpy as np
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype, is_numeric_dtype


def _normalize_date_column(series: pd.Series) -> pd.Series:
    values = series.reset_index(drop=True)
    non_missing = values.dropna()

    if non_missing.empty:
        return values

    if is_datetime64_any_dtype(non_missing):
        return pd.to_datetime(values, errors="coerce")

    numeric_values = pd.to_numeric(non_missing, errors="coerce")
    if is_numeric_dtype(non_missing) or numeric_values.notna().all():
        converted = pd.Series(pd.NaT, index=values.index, dtype="datetime64[ns]")
        converted.loc[non_missing.index] = pd.to_datetime(
            numeric_values,
            unit="D",
            origin="1899-12-30",
            errors="coerce",
        )
        return converted

    converted = pd.to_datetime(values, errors="coerce")
    return converted.where(converted.notna(), values)


def read_uploaded_xlsx(file_bytes: bytes) -> pd.DataFrame:
    """
    Read the first sheet from an uploaded xlsx file and enforce the input schema.
    """
    if not file_bytes:
        raise ValueError("上传文件为空。")

    try:
        raw_df = pd.read_excel(BytesIO(file_bytes), sheet_name=0, engine="openpyxl")
    except Exception as exc:
        raise ValueError(f"无法读取 xlsx 文件，请确认文件格式正确：{exc}") from exc

    if "y" not in raw_df.columns:
        raise ValueError('输入文件必须包含名为 "y" 的列。')

    output = pd.DataFrame(index=raw_df.index)
    if "date" in raw_df.columns:
        output["date"] = _normalize_date_column(raw_df["date"])

    y_values = pd.to_numeric(raw_df["y"], errors="coerce")
    if y_values.isna().any():
        raise ValueError('"y" 列必须为数值且不能包含缺失值。')

    output["y"] = y_values.astype("float64")
    return output.reset_index(drop=True)


def to_forecast_xlsx(
    forecasts: np.ndarray,
    dates: pd.Series | None = None,
) -> bytes:
    """
    Package forecast values into xlsx bytes using the grading output schema.
    """
    forecast_values = np.asarray(forecasts, dtype="float64").reshape(-1)
    output = pd.DataFrame({"y": forecast_values})

    if dates is not None:
        date_values = pd.Series(dates).reset_index(drop=True)
        if len(date_values) != len(output):
            raise ValueError("date 数量必须与预测值数量一致。")
        output.insert(0, "date", date_values)

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        output.to_excel(writer, sheet_name="Sheet1", index=False)
    return buffer.getvalue()


def read_uploaded_csv(file_bytes: bytes) -> pd.DataFrame:
    if not file_bytes:
        raise ValueError("上传文件为空。")
    return pd.read_csv(BytesIO(file_bytes))
