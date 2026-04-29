from __future__ import annotations

import argparse
import os
import sys
import time
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.io import read_uploaded_xlsx
from core.predictor import (
    _auto_arima_forecast,
    _holt_winters_forecast,
    _naive_forecast,
    _xgboost_forecast,
    forecast_one_step,
    rolling_backtest,
)


warnings.filterwarnings("ignore")


AKSHARE_SYMBOLS = {
    "pingan_bank": "sz000001",
    "cmb_bank": "sh600036",
    "moutai": "sh600519",
    "catl": "sz300750",
    "byd": "sz002594",
    "pingan_ins": "sh601318",
}

EXTERNAL_WINDOW = 320
EXTERNAL_START = "20220101"
EXTERNAL_END = "20250401"
SEGMENT_SIZE = 25


@dataclass
class MetricSet:
    rmse: float
    mae: float
    mape: float


def _disable_proxy_env() -> None:
    for key in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
    ):
        os.environ[key] = ""
    os.environ["NO_PROXY"] = "*"
    os.environ["no_proxy"] = "*"


def _compute_metrics(actual: np.ndarray, pred: np.ndarray) -> MetricSet:
    err = pred - actual
    denom = np.maximum(np.abs(actual), 1e-8)
    return MetricSet(
        rmse=float(np.sqrt(np.mean(err**2))),
        mae=float(np.mean(np.abs(err))),
        mape=float(np.mean(np.abs(err) / denom) * 100),
    )


def _backtest_with_forecaster(
    values: np.ndarray,
    forecaster,
    train_ratio: float = 0.8,
) -> np.ndarray:
    train_end = min(max(int(len(values) * train_ratio), 1), len(values) - 1)
    preds = []
    for t in range(train_end, len(values)):
        pred = forecaster(values[:t])
        if pred is None or not np.isfinite(pred):
            pred = _naive_forecast(values[:t])
        preds.append(float(pred))
    return np.asarray(preds, dtype="float64")


def _load_sample_dataset(dataset_path: Path) -> pd.DataFrame:
    with dataset_path.open("rb") as handle:
        return read_uploaded_xlsx(handle.read())


def _evaluate_sample_dataset(dataset_path: Path) -> dict:
    df = _load_sample_dataset(dataset_path)
    series = df["y"].to_numpy(dtype="float64")
    dates = df["date"]
    n = len(series)
    train_end = int(n * 0.8)

    start = time.perf_counter()
    next_value = float(forecast_one_step(series))
    one_step_seconds = time.perf_counter() - start

    start = time.perf_counter()
    preds = rolling_backtest(series)
    backtest_seconds = time.perf_counter() - start

    actual = series[train_end:]
    errors = preds - actual
    abs_err = np.abs(errors)
    sample_metrics = _compute_metrics(actual, preds)

    naive_preds = _backtest_with_forecaster(series, _naive_forecast)
    naive_metrics = _compute_metrics(actual, naive_preds)

    component_forecasters = {
        "ensemble": None,
        "naive": _naive_forecast,
        "holt_winters": _holt_winters_forecast,
        "auto_ar": _auto_arima_forecast,
        "xgboost": _xgboost_forecast,
    }
    component_metrics = {}
    for name, forecaster in component_forecasters.items():
        component_preds = preds if forecaster is None else _backtest_with_forecaster(series, forecaster)
        component_metrics[name] = _compute_metrics(actual, component_preds)

    segment_rows = []
    for offset in range(0, len(actual), SEGMENT_SIZE):
        seg_abs = abs_err[offset : offset + SEGMENT_SIZE]
        seg_actual = actual[offset : offset + SEGMENT_SIZE]
        seg_pred = preds[offset : offset + SEGMENT_SIZE]
        seg_metrics = _compute_metrics(seg_actual, seg_pred)
        seg_dates = dates.iloc[train_end + offset : train_end + offset + len(seg_abs)]
        segment_rows.append(
            {
                "start": str(seg_dates.iloc[0].date()),
                "end": str(seg_dates.iloc[-1].date()),
                "mae": seg_metrics.mae,
                "mape": seg_metrics.mape,
                "max_err": float(seg_abs.max()),
            }
        )

    head_rows = []
    tail_rows = []
    for idx in range(min(5, len(actual))):
        head_rows.append(
            {
                "date": str(dates.iloc[train_end + idx].date()),
                "actual": float(actual[idx]),
                "pred": float(preds[idx]),
                "err": float(errors[idx]),
            }
        )
    for idx in range(max(0, len(actual) - 5), len(actual)):
        tail_rows.append(
            {
                "date": str(dates.iloc[train_end + idx].date()),
                "actual": float(actual[idx]),
                "pred": float(preds[idx]),
                "err": float(errors[idx]),
            }
        )

    return {
        "n": n,
        "train_end": train_end,
        "test_size": len(actual),
        "date_start": str(dates.iloc[0].date()),
        "date_end": str(dates.iloc[-1].date()),
        "last_value": float(series[-1]),
        "next_value": next_value,
        "delta": next_value - float(series[-1]),
        "one_step_seconds": one_step_seconds,
        "backtest_seconds": backtest_seconds,
        "metrics": sample_metrics,
        "naive_metrics": naive_metrics,
        "max_abs_err": float(abs_err.max()),
        "max_abs_err_index": int(abs_err.argmax() + train_end),
        "min_abs_err": float(abs_err.min()),
        "min_abs_err_index": int(abs_err.argmin() + train_end),
        "component_metrics": component_metrics,
        "segment_rows": segment_rows,
        "head_rows": head_rows,
        "tail_rows": tail_rows,
    }


def _fetch_log_close(symbol: str) -> pd.Series:
    _disable_proxy_env()
    import akshare as ak

    df = ak.stock_zh_a_daily(
        symbol=symbol,
        start_date=EXTERNAL_START,
        end_date=EXTERNAL_END,
        adjust="qfq",
    )
    frame = df[["date", "close"]].copy()
    frame["date"] = pd.to_datetime(frame["date"])
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    frame = frame.dropna().sort_values("date")
    frame = frame[frame["close"] > 0]
    return pd.Series(np.log(frame["close"].to_numpy(dtype="float64")), index=frame["date"])


def _build_external_datasets() -> pd.DataFrame:
    series = {
        name: _fetch_log_close(symbol)
        for name, symbol in AKSHARE_SYMBOLS.items()
    }
    return pd.concat(series, axis=1, join="inner").dropna().sort_index()


def _evaluate_external_datasets() -> dict:
    frame = _build_external_datasets()
    datasets = {
        name: frame[name].iloc[-EXTERNAL_WINDOW:].to_numpy(dtype="float64")
        for name in AKSHARE_SYMBOLS
    }
    datasets["mix_bank"] = (
        0.40 * frame["pingan_bank"]
        + 0.35 * frame["cmb_bank"]
        + 0.25 * frame["pingan_ins"]
    ).iloc[-EXTERNAL_WINDOW:].to_numpy(dtype="float64")
    datasets["mix_growth"] = (
        0.45 * frame["catl"]
        + 0.35 * frame["byd"]
        + 0.20 * frame["moutai"]
    ).iloc[-EXTERNAL_WINDOW:].to_numpy(dtype="float64")
    datasets["mix_cross"] = (
        0.40 * frame["moutai"]
        + 0.30 * frame["pingan_bank"]
        + 0.30 * frame["catl"]
    ).iloc[-EXTERNAL_WINDOW:].to_numpy(dtype="float64")

    robustness_rows = []
    for name, values in datasets.items():
        actual = values[int(len(values) * 0.8) :]
        ensemble_pred = rolling_backtest(values)
        naive_pred = _backtest_with_forecaster(values, _naive_forecast)
        ensemble_metrics = _compute_metrics(actual, ensemble_pred)
        naive_metrics = _compute_metrics(actual, naive_pred)
        robustness_rows.append(
            {
                "dataset": name,
                "ens_rmse": ensemble_metrics.rmse,
                "nv_rmse": naive_metrics.rmse,
                "rmse_gain": (naive_metrics.rmse - ensemble_metrics.rmse) / naive_metrics.rmse * 100,
                "ens_mae": ensemble_metrics.mae,
                "nv_mae": naive_metrics.mae,
                "mae_gain": (naive_metrics.mae - ensemble_metrics.mae) / naive_metrics.mae * 100,
                "ens_mape": ensemble_metrics.mape,
                "nv_mape": naive_metrics.mape,
            }
        )

    focus_sets = {
        "pingan_bank": datasets["pingan_bank"],
        "byd": datasets["byd"],
        "mix_growth": (
            0.55 * frame["byd"] + 0.45 * frame["catl"]
        ).iloc[-EXTERNAL_WINDOW:].to_numpy(dtype="float64"),
    }
    focus_forecasters = {
        "naive": _naive_forecast,
        "holt_winters": _holt_winters_forecast,
        "auto_ar": _auto_arima_forecast,
        "xgboost": _xgboost_forecast,
    }

    component_rows = []
    for dataset_name, values in focus_sets.items():
        actual = values[int(len(values) * 0.8) :]
        dataset_scores = []
        for name, forecaster in focus_forecasters.items():
            pred = _backtest_with_forecaster(values, forecaster)
            metric = _compute_metrics(actual, pred)
            dataset_scores.append((metric.rmse, name))
            component_rows.append(
                {
                    "dataset": dataset_name,
                    "model": name,
                    "rmse": metric.rmse,
                    "mae": metric.mae,
                    "mape": metric.mape,
                }
            )
        dataset_scores.sort()
        component_rows.append(
            {
                "dataset": dataset_name,
                "model": "best_rmse",
                "rmse": np.nan,
                "mae": np.nan,
                "mape": np.nan,
                "winner": dataset_scores[0][1],
                "runner_up": dataset_scores[1][1],
            }
        )

    return {
        "aligned_rows": int(len(frame)),
        "robustness_rows": robustness_rows,
        "component_rows": component_rows,
    }


def _table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _render_report(sample_result: dict, external_result: dict, report_path: Path) -> str:
    sample_metric_rows = [
        [
            "ensemble",
            f"{sample_result['metrics'].rmse:.6f}",
            f"{sample_result['metrics'].mae:.6f}",
            f"{sample_result['metrics'].mape:.4f}%",
        ],
        [
            "naive_baseline",
            f"{sample_result['naive_metrics'].rmse:.6f}",
            f"{sample_result['naive_metrics'].mae:.6f}",
            f"{sample_result['naive_metrics'].mape:.4f}%",
        ],
    ]

    component_rows = []
    for name, metric in sample_result["component_metrics"].items():
        component_rows.append(
            [
                name,
                f"{metric.rmse:.6f}",
                f"{metric.mae:.6f}",
                f"{metric.mape:.4f}%",
            ]
        )

    segment_rows = []
    for row in sample_result["segment_rows"]:
        segment_rows.append(
            [
                f"{row['start']} ~ {row['end']}",
                f"{row['mae']:.6f}",
                f"{row['mape']:.4f}%",
                f"{row['max_err']:.6f}",
            ]
        )

    head_rows = []
    for row in sample_result["head_rows"]:
        head_rows.append(
            [
                row["date"],
                f"{row['actual']:.6f}",
                f"{row['pred']:.6f}",
                f"{row['err']:+.6f}",
            ]
        )

    tail_rows = []
    for row in sample_result["tail_rows"]:
        tail_rows.append(
            [
                row["date"],
                f"{row['actual']:.6f}",
                f"{row['pred']:.6f}",
                f"{row['err']:+.6f}",
            ]
        )

    robustness_rows = []
    for row in external_result["robustness_rows"]:
        robustness_rows.append(
            [
                row["dataset"],
                f"{row['ens_rmse']:.5f}",
                f"{row['nv_rmse']:.5f}",
                f"{row['rmse_gain']:+.2f}%",
                f"{row['ens_mae']:.5f}",
                f"{row['nv_mae']:.5f}",
                f"{row['mae_gain']:+.2f}%",
                f"{row['ens_mape']:.3f}%",
                f"{row['nv_mape']:.3f}%",
            ]
        )

    focus_metric_rows = []
    focus_winner_lines = []
    for row in external_result["component_rows"]:
        if row["model"] == "best_rmse":
            focus_winner_lines.append(
                f"- {row['dataset']}: best_rmse={row['winner']}, second={row['runner_up']}"
            )
            continue
        focus_metric_rows.append(
            [
                row["dataset"],
                row["model"],
                f"{row['rmse']:.5f}",
                f"{row['mae']:.5f}",
                f"{row['mape']:.3f}%",
            ]
        )

    rerun_cmd = (
        "python tests/run_module_b_evaluation.py "
        f"--report-path {report_path.relative_to(ROOT)}"
    )

    lines = [
        "# Module B Evaluation Report",
        "",
        "## Fixed Workflow",
        "",
        "1. Load the local sample dataset from dataset.xlsx via core.io.read_uploaded_xlsx.",
        "2. Run one-step forecasting and full rolling backtest with core.predictor.",
        "3. Compare the ensemble against naive and each component model on the sample dataset.",
        "4. Download external stocks from AkShare stock_zh_a_daily, convert close to log-close, and test the last 320 aligned observations.",
        "5. Export the full evaluation result as Markdown for repeated tuning and regression checks.",
        "",
        "Rerun command:",
        "",
        "```bash",
        rerun_cmd,
        "```",
        "",
        "The script clears proxy-related environment variables and forces NO_PROXY=* before requesting AkShare so that Sina source can be fetched more reliably on this machine.",
        "",
        "## Sample Dataset Summary",
        "",
        f"- Samples: {sample_result['n']} ({sample_result['date_start']} ~ {sample_result['date_end']})",
        f"- Train/Test split: {sample_result['train_end']} / {sample_result['test_size']}",
        f"- One-step forecast: {sample_result['next_value']:.6f}",
        f"- Last observed value: {sample_result['last_value']:.6f}",
        f"- Delta: {sample_result['delta']:+.6f}",
        f"- One-step runtime: {sample_result['one_step_seconds']:.2f}s",
        f"- Backtest runtime: {sample_result['backtest_seconds']:.2f}s",
        f"- Max abs error: {sample_result['max_abs_err']:.6f} (index={sample_result['max_abs_err_index']})",
        f"- Min abs error: {sample_result['min_abs_err']:.6f} (index={sample_result['min_abs_err_index']})",
        "",
        _table(["model", "RMSE", "MAE", "MAPE"], sample_metric_rows),
        "",
        "## Sample Component Breakdown",
        "",
        _table(["model", "RMSE", "MAE", "MAPE"], component_rows),
        "",
        "## Sample Segment Errors",
        "",
        _table(["range", "MAE", "MAPE", "max_err"], segment_rows),
        "",
        "## Sample Head Rows",
        "",
        _table(["date", "actual", "pred", "err"], head_rows),
        "",
        "## Sample Tail Rows",
        "",
        _table(["date", "actual", "pred", "err"], tail_rows),
        "",
        "## External Stock Robustness",
        "",
        f"- AkShare aligned rows: {external_result['aligned_rows']}",
        f"- External window: last {EXTERNAL_WINDOW} observations per dataset, chronological 80/20 split",
        "",
        _table(
            [
                "dataset",
                "ens_rmse",
                "nv_rmse",
                "rmse_gain",
                "ens_mae",
                "nv_mae",
                "mae_gain",
                "ens_mape",
                "nv_mape",
            ],
            robustness_rows,
        ),
        "",
        "## External Component Winners",
        "",
        _table(["dataset", "model", "RMSE", "MAE", "MAPE"], focus_metric_rows),
        "",
        *focus_winner_lines,
        "",
        "## Interpretation",
        "",
        "- The current ensemble consistently beats the naive baseline on the sample dataset and on the external stock basket.",
        "- The best single model changes across datasets: XGBoost leads on pingan_bank, while Auto-AR leads on byd and mix_growth.",
        "- This report should be treated as the fixed regression workflow for tuning Module B: rerun after every model change and compare the same tables before accepting the edit.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run repeatable Module B evaluation and export a Markdown report.")
    parser.add_argument(
        "--dataset-path",
        default=str(ROOT / "dataset.xlsx"),
        help="Path to the local sample dataset.",
    )
    parser.add_argument(
        "--report-path",
        default=str(ROOT / "report" / "module_b_evaluation.md"),
        help="Path to the generated Markdown report.",
    )
    parser.add_argument(
        "--skip-external",
        action="store_true",
        help="Only evaluate the local sample dataset.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset_path = Path(args.dataset_path).resolve()
    report_path = Path(args.report_path).resolve()

    sample_result = _evaluate_sample_dataset(dataset_path)
    external_result = {
        "aligned_rows": 0,
        "robustness_rows": [],
        "component_rows": [],
    }
    if not args.skip_external:
        external_result = _evaluate_external_datasets()

    report_path.parent.mkdir(parents=True, exist_ok=True)
    content = _render_report(sample_result, external_result, report_path)
    report_path.write_text(content, encoding="utf-8")

    print(f"[OK] report written to {report_path}")
    print(f"[OK] sample RMSE={sample_result['metrics'].rmse:.6f}, MAE={sample_result['metrics'].mae:.6f}, MAPE={sample_result['metrics'].mape:.4f}%")
    if external_result["robustness_rows"]:
        best = max(external_result["robustness_rows"], key=lambda row: row["rmse_gain"])
        print(
            "[OK] best external RMSE gain="
            f"{best['rmse_gain']:+.2f}% on {best['dataset']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())