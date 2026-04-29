from __future__ import annotations

import os
import warnings

import numpy as np
import pandas as pd

from core.config import DEFAULT_THRESHOLD


_ENSEMBLE_WEIGHTS = {
    "holt_winters": 0.05,
    "arima": 0.75,
    "xgboost": 0.20,
}
_MAX_LAG = 20
_MIN_XGB_SERIES_LENGTH = 30
_ETS_CONFIGS = (
    {"trend": "add", "damped_trend": True},
    {"trend": "add", "damped_trend": False},
    {"trend": None, "damped_trend": False},
)


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def _as_clean_series(series: np.ndarray) -> np.ndarray:
    values = np.asarray(series, dtype="float64").reshape(-1)
    if values.size == 0:
        raise ValueError("时间序列为空，无法预测。")
    if not np.isfinite(values).all():
        raise ValueError("时间序列必须只包含有限数值。")
    return values


def _naive_forecast(series: np.ndarray) -> float:
    if series.size == 1:
        return float(series[-1])

    recent_window = min(5, series.size)
    recent_level = float(np.mean(series[-recent_window:]))
    last_delta = float(series[-1] - series[-2])
    return recent_level + 0.5 * last_delta


def _holt_winters_forecast(series: np.ndarray) -> float | None:
    if series.size < 3:
        return None

    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing

        best: tuple[float, float] | None = None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with np.errstate(all="ignore"):
                for config in _ETS_CONFIGS:
                    try:
                        model = ExponentialSmoothing(
                            series,
                            trend=config["trend"],
                            damped_trend=bool(config["damped_trend"]),
                            seasonal=None,
                            initialization_method="estimated",
                        )
                        fit = model.fit(optimized=True, remove_bias=True)
                        pred = float(fit.forecast(1)[0])
                        aic = float(getattr(fit, "aic", np.inf))
                    except Exception:
                        continue

                    if np.isfinite(pred) and (best is None or aic < best[1]):
                        best = (pred, aic)

        if best is None:
            return None
        return best[0]
    except Exception:
        return None


def _fit_ar_next(values: np.ndarray, order: int) -> tuple[float, float] | None:
    if values.size < max(order + 2, 3):
        return None

    if order == 0:
        pred = float(np.mean(values))
        resid = values - pred
        sigma2 = max(float(np.mean(resid**2)), 1e-12)
        aic = values.size * np.log(sigma2) + 2
        return pred, float(aic)

    x_rows = []
    y_values = []
    for idx in range(order, values.size):
        x_rows.append(np.r_[1.0, values[idx - order : idx][::-1]])
        y_values.append(values[idx])

    x_train = np.vstack(x_rows)
    y_train = np.asarray(y_values, dtype="float64")
    try:
        beta = np.linalg.lstsq(x_train, y_train, rcond=None)[0]
    except Exception:
        return None

    residuals = y_train - x_train @ beta
    sigma2 = max(float(np.mean(residuals**2)), 1e-12)
    aic = len(y_train) * np.log(sigma2) + 2 * len(beta)
    x_next = np.r_[1.0, values[-order:][::-1]]
    return float(x_next @ beta), float(aic)


def _numpy_auto_arima_forecast(series: np.ndarray) -> float | None:
    if series.size < 8:
        return None

    best: tuple[float, float] | None = None
    max_order = min(8, max(1, series.size // 8))

    for differencing in (0, 1, 2):
        values = np.diff(series, n=differencing) if differencing else series
        if values.size < 3:
            continue

        for order in range(0, max_order + 1):
            fitted = _fit_ar_next(values, order)
            if fitted is None:
                continue

            pred, aic = fitted
            if differencing == 0:
                next_value = float(pred)
            elif differencing == 1:
                next_value = float(series[-1] + pred)
            else:
                next_value = float(2 * series[-1] - series[-2] + pred)
            if best is None or aic < best[1]:
                best = (next_value, aic)

    if best is None:
        return None
    return best[0]


def _auto_arima_forecast(series: np.ndarray) -> float | None:
    if series.size < 8:
        return None

    if os.getenv("PREDICT_USE_PMDARIMA") == "1":
        try:
            import pmdarima as pm

            max_order = 3 if series.size < 50 else 5
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model = pm.auto_arima(
                    series,
                    start_p=1,
                    start_q=1,
                    max_p=max_order,
                    max_q=max_order,
                    d=None,
                    seasonal=False,
                    information_criterion="aic",
                    stepwise=True,
                    error_action="ignore",
                    suppress_warnings=True,
                )
            return float(model.predict(n_periods=1)[0])
        except Exception:
            pass

    return _numpy_auto_arima_forecast(series)


def _lag_count(series_length: int) -> int:
    return max(1, min(_MAX_LAG, series_length - 1))


def _features_from_history(history: np.ndarray, lag_count: int) -> np.ndarray:
    features: list[float] = []

    for lag in range(1, lag_count + 1):
        if history.size >= lag:
            features.append(float(history[-lag]))
        else:
            features.append(float(history[0]))

    for window in (5, 10):
        values = history[-min(window, history.size) :]
        features.append(float(np.mean(values)))
        features.append(float(np.std(values, ddof=0)))

    if history.size >= 2:
        features.append(float(history[-1] - history[-2]))
    else:
        features.append(0.0)

    if history.size >= 3:
        features.append(float(history[-2] - history[-3]))
    else:
        features.append(0.0)

    return np.asarray(features, dtype="float64")


def _build_lag_dataset(series: np.ndarray, lag_count: int) -> tuple[np.ndarray, np.ndarray]:
    rows: list[np.ndarray] = []
    targets: list[float] = []

    for target_idx in range(1, series.size):
        history = series[:target_idx]
        rows.append(_features_from_history(history, lag_count))
        targets.append(float(series[target_idx]))

    return np.vstack(rows), np.asarray(targets, dtype="float64")


def _xgboost_forecast(series: np.ndarray) -> float | None:
    if series.size < _MIN_XGB_SERIES_LENGTH:
        return None

    try:
        import xgboost as xgb
    except Exception:
        return None

    lag_count = _lag_count(series.size)
    try:
        x_train, y_train = _build_lag_dataset(series, lag_count)
        if len(y_train) < 5:
            return None

        model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="reg:squarederror",
            random_state=42,
            n_jobs=1,
            verbosity=0,
        )
        model.fit(x_train, y_train)
        x_pred = _features_from_history(series, lag_count).reshape(1, -1)
        return float(model.predict(x_pred)[0])
    except Exception:
        return None


def forecast_one_step(series: np.ndarray) -> float:
    """
    Forecast the next value y_{N+1} using only y[0..N-1].

    The ensemble prefers Holt-Winters, Auto-ARIMA, and XGBoost lag features.
    Failed or skipped models are removed and the remaining weights are
    renormalized. A local naive forecast is used only when every model fails.
    """
    values = _as_clean_series(series)

    candidates = {
        "holt_winters": _holt_winters_forecast(values),
        "arima": _auto_arima_forecast(values),
        "xgboost": _xgboost_forecast(values),
    }
    usable = {
        name: pred
        for name, pred in candidates.items()
        if pred is not None and np.isfinite(pred)
    }

    if not usable:
        return _naive_forecast(values)

    weight_sum = sum(_ENSEMBLE_WEIGHTS[name] for name in usable)
    forecast = sum(
        (_ENSEMBLE_WEIGHTS[name] / weight_sum) * float(pred)
        for name, pred in usable.items()
    )
    return float(forecast)


def rolling_backtest(
    series: np.ndarray,
    train_ratio: float = 0.8,
) -> np.ndarray:
    """
    Walk-forward one-step backtest with no future leakage.

    For every test index t, the forecast is computed from series[:t] only.
    The output length is N - floor(train_ratio * N), matching the 20% test
    segment for the default 80/20 chronological split.
    """
    values = _as_clean_series(series)
    if not 0 < float(train_ratio) < 1:
        raise ValueError("train_ratio 必须位于 0 和 1 之间。")
    if values.size < 2:
        raise ValueError("至少需要 2 个样本才能进行滚动回测。")

    train_end = int(values.size * float(train_ratio))
    train_end = min(max(train_end, 1), values.size - 1)

    preds = [forecast_one_step(values[:t]) for t in range(train_end, values.size)]
    return np.asarray(preds, dtype="float64")


def predict_dataframe(df: pd.DataFrame, threshold: float = DEFAULT_THRESHOLD) -> pd.DataFrame:
    if df is None or df.empty:
        raise ValueError("数据为空，无法预测。")

    if "y" in df.columns:
        forecasts = rolling_backtest(df["y"].to_numpy(dtype="float64"))
        output = pd.DataFrame({"y": forecasts})
        if "date" in df.columns:
            test_start = len(df) - len(output)
            output.insert(0, "date", df["date"].iloc[test_start:].reset_index(drop=True))
        return output

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if not numeric_cols:
        raise ValueError("CSV 中没有可用于预测的数值列。")

    features = df[numeric_cols].fillna(0.0)
    row_signal = features.mean(axis=1).to_numpy(dtype=float)
    prob = _sigmoid(row_signal)
    label = (prob >= float(threshold)).astype(int)

    output = df.copy()
    output["prediction_score"] = prob.round(6)
    output["prediction_label"] = label
    return output
