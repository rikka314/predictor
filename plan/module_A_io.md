# Module A — core/io.py + core/config.py

> 状态：已完成（2026-04-29）
> 验证：`python -m pytest tests/test_io.py`

## 负责范围
数据层：xlsx 读取验证、结果写出

## 目标文件
- `core/io.py`
- `core/config.py`

## 接口规范

```python
# core/config.py
TRAIN_RATIO: float = 0.8          # 训练集比例

# core/io.py
def read_uploaded_xlsx(file_bytes: bytes) -> pd.DataFrame:
    """
    读取第一个 sheet。
    必须包含列 "y"（数值，无缺失）。
    可包含列 "date"（任意日期格式，仅用于对齐输出）。
    若校验失败抛出 ValueError，附带中文说明。
    返回 DataFrame，index 为 0..N-1，列为 ["y"] 或 ["date","y"]。
    """

def to_forecast_xlsx(
    forecasts: np.ndarray,
    dates: pd.Series | None = None,
) -> bytes:
    """
    将预测值打包为 xlsx bytes。
    output schema: 列 "y"（必须），列 "date"（若 dates 不为 None）。
    行顺序与 forecasts 一致。
    """
```

## 实现细节
1. 使用 `openpyxl` 引擎读取（`pd.read_excel(..., engine="openpyxl")`）
2. 检查 `y` 列：存在 → 转 float64 → 检查 NaN → 若有则 raise ValueError
3. `date` 列：`pd.to_datetime(..., infer_datetime_format=True, errors="coerce")`，转换失败则仍保留原始字符串（不报错）
4. `to_forecast_xlsx` 用 `BytesIO` + `pd.ExcelWriter` 写出，sheet 名 "Sheet1"

## 依赖
```
pandas>=2.0.0
openpyxl>=3.1.0
numpy>=1.24.0
```

## 测试要点
- 正常 xlsx（含 date + y）→ 正确解析
- y 有 NaN → 抛出 ValueError 含 "缺失值"
- 无 y 列 → 抛出 ValueError 含 "y"
- 纯数字 date 列（Excel serial）→ 正确转为日期
