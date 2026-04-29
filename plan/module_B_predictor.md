# Module B — core/predictor.py

## 负责范围
预测引擎（影响 30 分精度评分）

## 目标文件
- `core/predictor.py`

## 公共接口

```python
def forecast_one_step(series: np.ndarray) -> float:
    """
    输入：完整时间序列 y[0..N-1]
    输出：单个 float，即 y_{N+1} 的预测值
    无副作用，不依赖外部状态。
    """

def rolling_backtest(
    series: np.ndarray,
    train_ratio: float = 0.8,
) -> np.ndarray:
    """
    输入：完整时间序列
    输出：长度为 ceil((1-train_ratio)*N) 的预测数组
    严格滚动：预测 y_t 时只能用 y[0..t-1]，绝不使用 y[t] 及以后。
    """
```

## 模型栈

### M1: Holt-Winters 指数平滑
```python
from statsmodels.tsa.holtwinters import ExponentialSmoothing

model = ExponentialSmoothing(
    train,
    trend="add",
    damped_trend=True,
    seasonal=None,          # 序列较短时不加季节项
    initialization_method="estimated",
)
fit = model.fit(optimized=True, remove_bias=True)
pred = fit.forecast(1)[0]
```

### M2: Auto-ARIMA
```python
import pmdarima as pm

model = pm.auto_arima(
    train,
    start_p=1, start_q=1,
    max_p=5, max_q=5,
    d=None,                 # 自动检验单位根
    seasonal=False,
    information_criterion="aic",
    stepwise=True,
    error_action="ignore",
    suppress_warnings=True,
)
pred = model.predict(1)[0]
```

### M3: XGBoost + lag features
```python
import xgboost as xgb

# 特征：lags 1-20, rolling_mean(5), rolling_mean(10),
#        rolling_std(5), rolling_std(10), diff(1), diff(2)
# 若序列长度 < 25，则只取可用 lags
def make_features(series, max_lag=20):
    ...

X_train, y_train = build_dataset(train_series)
model = xgb.XGBRegressor(
    n_estimators=200,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
)
model.fit(X_train, y_train)
x_pred = make_last_features(full_series_so_far)
pred = model.predict(x_pred)[0]
```

### 集成策略
- Phase1 最终权重：HW=0.05, ARIMA=0.75, XGB=0.20（基于 `report/module_b_evaluation_final.md` 的 sample RMSE 优化）
- 若 M1 拟合失败（异常），退出权重平分到 M2/M3
- 若 M2 拟合失败，退出权重平分到 M1/M3
- 若序列长度 < 30，跳过 XGB，仅用 M1+M2 均值

```python
final_pred = w1*p1 + w2*p2 + w3*p3
```

## 滚动回测实现
```python
def rolling_backtest(series, train_ratio=0.8):
    n = len(series)
    train_end = int(n * train_ratio)
    preds = []
    for t in range(train_end, n):
        hist = series[:t]          # 严格只用 t 之前的数据
        preds.append(forecast_one_step(hist))
    return np.array(preds)
```

## 依赖
```
statsmodels>=0.14.0
xgboost>=2.0.0
scikit-learn>=1.3.0   # XGBoost sklearn API
numpy>=1.24.0
```

实现备注：默认 ARIMA 分支使用纯 `numpy` 的 AIC 自动 AR/差分选择，避免 `statsmodels.ARIMA.fit()` 与 `pmdarima` 在 Python 3.13 环境中的二进制兼容风险；如部署环境已验证 `pmdarima` 可用，可通过 `PREDICT_USE_PMDARIMA=1` 启用原生 Auto-ARIMA。

## 性能注意
- 滚动回测调用 N*0.2 次 `forecast_one_step`，每次 auto_arima 约 0.3-1s
- 数据集约 200-500 行，test 40-100 次，总时间约 30-120s，在 UI 加 spinner

## 测试要点
- `forecast_one_step` 返回单个 float
- `rolling_backtest` 长度 == ceil(0.2*N)，无 NaN
- 严格无数据泄漏：series[train_end:] 不被用于训练

## 完成状态
- 已实现 `forecast_one_step(series) -> float`
- 已实现 `rolling_backtest(series, train_ratio=0.8) -> np.ndarray`
- 已接入 Holt-Winters、自动 AR/差分选择、XGBoost lag features 的集成预测
