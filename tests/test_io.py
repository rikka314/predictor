from __future__ import annotations

from io import BytesIO

import numpy as np
import pandas as pd
import pytest

from core.io import read_uploaded_xlsx, to_forecast_xlsx


def _xlsx_bytes(df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Sheet1", index=False)
    return buffer.getvalue()


def test_read_uploaded_xlsx_parses_date_and_y() -> None:
    df = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-02"],
            "y": [1, 2.5],
            "ignored": ["a", "b"],
        }
    )

    parsed = read_uploaded_xlsx(_xlsx_bytes(df))

    assert parsed.columns.tolist() == ["date", "y"]
    assert parsed.index.tolist() == [0, 1]
    assert parsed["y"].dtype == "float64"
    assert parsed["y"].tolist() == [1.0, 2.5]
    assert parsed["date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2026-01-01",
        "2026-01-02",
    ]


def test_read_uploaded_xlsx_rejects_missing_y_values() -> None:
    df = pd.DataFrame({"date": ["2026-01-01", "2026-01-02"], "y": [1.0, None]})

    with pytest.raises(ValueError, match="缺失值"):
        read_uploaded_xlsx(_xlsx_bytes(df))


def test_read_uploaded_xlsx_rejects_missing_y_column() -> None:
    df = pd.DataFrame({"date": ["2026-01-01"], "value": [1.0]})

    with pytest.raises(ValueError, match="y"):
        read_uploaded_xlsx(_xlsx_bytes(df))


def test_read_uploaded_xlsx_converts_excel_serial_dates() -> None:
    df = pd.DataFrame({"date": [45292, 45293], "y": [10, 11]})

    parsed = read_uploaded_xlsx(_xlsx_bytes(df))

    assert parsed["date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2024-01-01",
        "2024-01-02",
    ]


def test_read_uploaded_xlsx_preserves_excel_datetime_cells() -> None:
    df = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=2, freq="D"),
            "y": [10, 11],
        }
    )

    parsed = read_uploaded_xlsx(_xlsx_bytes(df))

    assert parsed["date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2026-01-01",
        "2026-01-02",
    ]


def test_to_forecast_xlsx_writes_forecasts_with_optional_dates() -> None:
    output = to_forecast_xlsx(
        np.array([1.25, 2.5]),
        dates=pd.Series(pd.to_datetime(["2026-01-03", "2026-01-04"])),
    )

    parsed = pd.read_excel(BytesIO(output), engine="openpyxl")

    assert parsed.columns.tolist() == ["date", "y"]
    assert parsed["y"].tolist() == [1.25, 2.5]
    assert parsed["date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2026-01-03",
        "2026-01-04",
    ]
