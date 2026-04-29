# Module B Evaluation Report

## Fixed Workflow

1. Load the local sample dataset from dataset.xlsx via core.io.read_uploaded_xlsx.
2. Run one-step forecasting and full rolling backtest with core.predictor.
3. Compare the ensemble against naive and each component model on the sample dataset.
4. Download external stocks from AkShare stock_zh_a_daily, convert close to log-close, and test the last 320 aligned observations.
5. Export the full evaluation result as Markdown for repeated tuning and regression checks.

Rerun command:

```bash
python tests/run_module_b_evaluation.py --report-path report/module_b_evaluation.md
```

The script clears proxy-related environment variables and forces NO_PROXY=* before requesting AkShare so that Sina source can be fetched more reliably on this machine.

## Sample Dataset Summary

- Samples: 500 (2024-03-18 ~ 2026-04-24)
- Train/Test split: 400 / 100
- One-step forecast: 1.354341
- Last observed value: 1.354252
- Delta: +0.000089
- One-step runtime: 0.89s
- Backtest runtime: 12.88s
- Max abs error: 0.014304 (index=445)
- Min abs error: 0.000068 (index=462)

| model | RMSE | MAE | MAPE |
|---|---|---|---|
| ensemble | 0.004135 | 0.003262 | 0.2398% |
| naive_baseline | 0.004767 | 0.003688 | 0.2710% |

## Sample Component Breakdown

| model | RMSE | MAE | MAPE |
|---|---|---|---|
| ensemble | 0.004135 | 0.003262 | 0.2398% |
| naive | 0.004767 | 0.003688 | 0.2710% |
| holt_winters | 0.004247 | 0.003428 | 0.2520% |
| auto_ar | 0.004118 | 0.003291 | 0.2420% |
| xgboost | 0.004339 | 0.003332 | 0.2450% |

## Sample Segment Errors

| range | MAE | MAPE | max_err |
|---|---|---|---|
| 2025-11-25 ~ 2025-12-29 | 0.002425 | 0.1788% | 0.007543 |
| 2025-12-30 ~ 2026-02-04 | 0.004262 | 0.3126% | 0.014304 |
| 2026-02-05 ~ 2026-03-19 | 0.002831 | 0.2074% | 0.006659 |
| 2026-03-20 ~ 2026-04-24 | 0.003530 | 0.2605% | 0.009939 |

## Sample Head Rows

| date | actual | pred | err |
|---|---|---|---|
| 2025-11-25 | 1.346795 | 1.345879 | -0.000915 |
| 2025-11-26 | 1.345596 | 1.346413 | +0.000817 |
| 2025-11-27 | 1.345118 | 1.345918 | +0.000799 |
| 2025-11-28 | 1.342740 | 1.346489 | +0.003749 |
| 2025-12-01 | 1.345741 | 1.344358 | -0.001383 |

## Sample Tail Rows

| date | actual | pred | err |
|---|---|---|---|
| 2026-04-20 | 1.352891 | 1.350289 | -0.002602 |
| 2026-04-21 | 1.351647 | 1.353375 | +0.001728 |
| 2026-04-22 | 1.350977 | 1.352781 | +0.001804 |
| 2026-04-23 | 1.351868 | 1.352068 | +0.000200 |
| 2026-04-24 | 1.354252 | 1.352966 | -0.001286 |

## External Stock Robustness

- AkShare aligned rows: 784
- External window: last 320 observations per dataset, chronological 80/20 split

| dataset | ens_rmse | nv_rmse | rmse_gain | ens_mae | nv_mae | mae_gain | ens_mape | nv_mape |
|---|---|---|---|---|---|---|---|---|
| pingan_bank | 0.00995 | 0.01168 | +14.78% | 0.00730 | 0.00904 | +19.23% | 0.305% | 0.378% |
| cmb_bank | 0.01413 | 0.01653 | +14.50% | 0.01055 | 0.01246 | +15.33% | 0.288% | 0.340% |
| moutai | 0.01296 | 0.01646 | +21.26% | 0.00925 | 0.01246 | +25.75% | 0.127% | 0.171% |
| catl | 0.01832 | 0.01985 | +7.70% | 0.01458 | 0.01627 | +10.38% | 0.264% | 0.295% |
| byd | 0.02722 | 0.03674 | +25.90% | 0.01990 | 0.02632 | +24.39% | 0.424% | 0.560% |
| pingan_ins | 0.01356 | 0.01566 | +13.40% | 0.01007 | 0.01234 | +18.41% | 0.259% | 0.317% |
| mix_bank | 0.01001 | 0.01166 | +14.11% | 0.00779 | 0.00972 | +19.92% | 0.243% | 0.303% |
| mix_growth | 0.01800 | 0.02076 | +13.31% | 0.01401 | 0.01611 | +13.05% | 0.251% | 0.289% |
| mix_cross | 0.01133 | 0.01252 | +9.54% | 0.00876 | 0.00984 | +10.98% | 0.166% | 0.186% |

## External Component Winners

| dataset | model | RMSE | MAE | MAPE |
|---|---|---|---|---|
| pingan_bank | naive | 0.01168 | 0.00904 | 0.378% |
| pingan_bank | holt_winters | 0.01049 | 0.00762 | 0.318% |
| pingan_bank | auto_ar | 0.01036 | 0.00745 | 0.311% |
| pingan_bank | xgboost | 0.01026 | 0.00763 | 0.319% |
| byd | naive | 0.03674 | 0.02632 | 0.560% |
| byd | holt_winters | 0.02638 | 0.01903 | 0.405% |
| byd | auto_ar | 0.02629 | 0.01894 | 0.403% |
| byd | xgboost | 0.03681 | 0.02761 | 0.587% |
| mix_growth | naive | 0.02573 | 0.01986 | 0.392% |
| mix_growth | holt_winters | 0.02054 | 0.01525 | 0.301% |
| mix_growth | auto_ar | 0.02046 | 0.01523 | 0.301% |
| mix_growth | xgboost | 0.02812 | 0.02225 | 0.439% |

- pingan_bank: best_rmse=xgboost, second=auto_ar
- byd: best_rmse=auto_ar, second=holt_winters
- mix_growth: best_rmse=auto_ar, second=holt_winters

## Interpretation

- The current ensemble consistently beats the naive baseline on the sample dataset and on the external stock basket.
- The best single model changes across datasets: XGBoost leads on pingan_bank, while Auto-AR leads on byd and mix_growth.
- This report should be treated as the fixed regression workflow for tuning Module B: rerun after every model change and compare the same tables before accepting the edit.
