# Frontend Contracts（Predict）

> 最近更新：2026-04-29  
> 适用范围：`app.py`、`ui/predict_page.py`、`ui/theme.py`

## 推荐读取顺序

1. `AI_CONTEXT.md`
2. `document/FRONTEND_STYLE_STANDARD.md`
3. 本文档

## 路由壳层：`app.py`

### 公开页面

当前公开路径：

- `/predict`

### 壳层职责

- 设置页面配置（标题、图标、布局）
- 注入全局主题样式
- 挂载预测页面入口 `render_predict_page()`

## 预测页 contract：`ui/predict_page.py`

### 页面入口

```python
render_predict_page() -> None
```

### 输入 contract

- 文件输入：Excel（`.xlsx`，通过 `st.file_uploader`）
- 数据约束：首个 sheet，必含 `y`，可选 `date`
- 触发约束：上传后自动执行 Part 1 + Part 2（不依赖额外按钮）
- 可调参数：允许存在，但不能阻断“上传即计算”的评分要求

### 输出 contract

- 原始数据预览
- Part 1：单个一步预测值（`y_{N+1}`）
- Part 2：滚动回测结果（测试区间逐点 one-step 预测）
- 评估指标：`RMSE`、`MAE`、`MAPE`
- 下载按钮：`backtest_forecasts.xlsx`

## 数据读取 contract：`core/io.py`

### 入口

```python
read_uploaded_xlsx(file_bytes: bytes) -> pd.DataFrame
to_forecast_xlsx(forecasts, dates=None) -> bytes
```

### 行为约定

- 读取第一个 sheet
- 缺失 `y` 列时报错
- `y` 列含缺失值时报错
- `date` 仅用于展示与输出对齐，不参与建模

## 预测 contract：`core/predictor.py`

### 入口

```python
forecast_one_step(series) -> float
rolling_backtest(series, train_ratio=0.8) -> np.ndarray
```

### 输入要求

- 输入序列按时间从旧到新
- rolling 回测必须严格使用历史窗口，禁止未来信息

### 返回要求

- `forecast_one_step` 返回单一数值预测
- `rolling_backtest` 返回测试段同长度预测数组
- 与输出文件 contract 对齐：`y`（必需）+ `date`（可选）

## 主题 contract：`ui/theme.py`

- `inject_global_styles()` 为当前站点级样式唯一入口
- 新增全局视觉语义优先在该文件沉淀
