# Module B Evaluation Report

## Fixed Workflow

1. Load the local sample dataset from dataset.xlsx via core.io.read_uploaded_xlsx.
2. Run one-step forecasting and full rolling backtest with core.predictor.
3. Compare the ensemble against naive and each component model on the sample dataset.
4. Download external stocks from AkShare stock_zh_a_daily, convert close to log-close, and test the last 320 aligned observations.
5. Export the full evaluation result as Markdown for repeated tuning and regression checks.

Rerun command:

```bash
python tests/run_module_b_evaluation.py --report-path report/module_b_evaluation_final.md
```

The script clears proxy-related environment variables and forces NO_PROXY=* before requesting AkShare so that Sina source can be fetched more reliably on this machine.

## Sample Dataset Summary

- Samples: 500 (2024-03-18 ~ 2026-04-24)
- Train/Test split: 400 / 100
- One-step forecast: 1.354736
- Last observed value: 1.354252
- Delta: +0.000484
- One-step runtime: 1.04s
- Backtest runtime: 16.08s
- Max abs error: 0.013875 (index=445)
- Min abs error: 0.000091 (index=400)

| model | RMSE | MAE | MAPE |
|---|---|---|---|
| ensemble | 0.004106 | 0.003240 | 0.2382% |
| naive_baseline | 0.004767 | 0.003688 | 0.2710% |

## Sample Component Breakdown

| model | RMSE | MAE | MAPE |
|---|---|---|---|
| ensemble | 0.004106 | 0.003240 | 0.2382% |
| naive | 0.004767 | 0.003688 | 0.2710% |
| holt_winters | 0.004244 | 0.003434 | 0.2525% |
| auto_ar | 0.004118 | 0.003291 | 0.2420% |
| xgboost | 0.004339 | 0.003332 | 0.2450% |

## Sample Segment Errors

| range | MAE | MAPE | max_err |
|---|---|---|---|
| 2025-11-25 ~ 2025-12-29 | 0.002509 | 0.1850% | 0.007319 |
| 2025-12-30 ~ 2026-02-04 | 0.004220 | 0.3095% | 0.013875 |
| 2026-02-05 ~ 2026-03-19 | 0.002711 | 0.1986% | 0.007509 |
| 2026-03-20 ~ 2026-04-24 | 0.003520 | 0.2598% | 0.009569 |

## Sample Head Rows

| date | actual | pred | err |
|---|---|---|---|
| 2025-11-25 | 1.346795 | 1.346885 | +0.000091 |
| 2025-11-26 | 1.345596 | 1.347442 | +0.001846 |
| 2025-11-27 | 1.345118 | 1.346757 | +0.001638 |
| 2025-11-28 | 1.342740 | 1.347012 | +0.004272 |
| 2025-12-01 | 1.345741 | 1.344913 | -0.000828 |

## Sample Tail Rows

| date | actual | pred | err |
|---|---|---|---|
| 2026-04-20 | 1.352891 | 1.350499 | -0.002391 |
| 2026-04-21 | 1.351647 | 1.353754 | +0.002107 |
| 2026-04-22 | 1.350977 | 1.352945 | +0.001968 |
| 2026-04-23 | 1.351868 | 1.352296 | +0.000428 |
| 2026-04-24 | 1.354252 | 1.353160 | -0.001092 |

## External Stock Robustness

- AkShare aligned rows: 784
- External window: last 320 observations per dataset, chronological 80/20 split

| dataset | ens_rmse | nv_rmse | rmse_gain | ens_mae | nv_mae | mae_gain | ens_mape | nv_mape |
|---|---|---|---|---|---|---|---|---|
| pingan_bank | 0.01002 | 0.01168 | +14.16% | 0.00728 | 0.00904 | +19.41% | 0.304% | 0.378% |
| cmb_bank | 0.01350 | 0.01653 | +18.36% | 0.00998 | 0.01246 | +19.87% | 0.273% | 0.340% |
| moutai | 0.01294 | 0.01646 | +21.39% | 0.00923 | 0.01246 | +25.96% | 0.127% | 0.171% |
| catl | 0.01842 | 0.01985 | +7.16% | 0.01473 | 0.01627 | +9.48% | 0.267% | 0.295% |
| byd | 0.02671 | 0.03674 | +27.32% | 0.01943 | 0.02632 | +26.17% | 0.414% | 0.560% |
| pingan_ins | 0.01344 | 0.01566 | +14.18% | 0.00987 | 0.01234 | +20.00% | 0.254% | 0.317% |
| mix_bank | 0.00989 | 0.01166 | +15.16% | 0.00769 | 0.00972 | +20.95% | 0.239% | 0.303% |
| mix_growth | 0.01761 | 0.02076 | +15.15% | 0.01351 | 0.01611 | +16.12% | 0.242% | 0.289% |
| mix_cross | 0.01123 | 0.01252 | +10.31% | 0.00870 | 0.00984 | +11.53% | 0.165% | 0.186% |

## External Component Winners

| dataset | model | RMSE | MAE | MAPE |
|---|---|---|---|---|
| pingan_bank | naive | 0.01168 | 0.00904 | 0.378% |
| pingan_bank | holt_winters | 0.01040 | 0.00753 | 0.315% |
| pingan_bank | auto_ar | 0.01036 | 0.00745 | 0.311% |
| pingan_bank | xgboost | 0.01026 | 0.00763 | 0.319% |
| byd | naive | 0.03674 | 0.02632 | 0.560% |
| byd | holt_winters | 0.02630 | 0.01894 | 0.403% |
| byd | auto_ar | 0.02629 | 0.01894 | 0.403% |
| byd | xgboost | 0.03681 | 0.02761 | 0.587% |
| mix_growth | naive | 0.02573 | 0.01986 | 0.392% |
| mix_growth | holt_winters | 0.02049 | 0.01521 | 0.300% |
| mix_growth | auto_ar | 0.02046 | 0.01523 | 0.301% |
| mix_growth | xgboost | 0.02812 | 0.02225 | 0.439% |

- pingan_bank: best_rmse=xgboost, second=auto_ar
- byd: best_rmse=auto_ar, second=holt_winters
- mix_growth: best_rmse=auto_ar, second=holt_winters

## Interpretation

- The current ensemble consistently beats the naive baseline on the sample dataset and on the external stock basket.
- The best single model changes across datasets: XGBoost leads on pingan_bank, while Auto-AR leads on byd and mix_growth.
- This report should be treated as the fixed regression workflow for tuning Module B: rerun after every model change and compare the same tables before accepting the edit.
