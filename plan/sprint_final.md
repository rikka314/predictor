# 最终冲刺计划（考试最后 1 小时）— v2（基于实测报告修订）

> 时间窗口：剩余 60 min  
> 策略：前 30 min 做精度优化，后 30 min 冻结功能、仅 debug + 部署验证  
> 原则：**基础 70 分零风险** → 精度 30 分最大化  
> 回归基线：`python tests/run_module_b_evaluation.py --report-path report/module_b_evaluation.md`

---

## 实测基线（优化前数据）

| model | RMSE | MAE | MAPE |
|-------|------|-----|------|
| ensemble | 0.004135 | 0.003262 | 0.2398% |
| auto_ar | 0.004118 | 0.003291 | 0.2420% |
| holt_winters | 0.004247 | 0.003428 | 0.2520% |
| xgboost | 0.004339 | 0.003332 | 0.2450% |
| naive | 0.004767 | 0.003688 | 0.2710% |

### 报告揭示的关键事实

1. **auto_ar 是当前最强单模型**：RMSE 0.004118 比 ensemble 的 0.004135 还低
2. **XGBoost 不稳定且整体偏弱**：sample 上最差，byd 外部数据上甚至劣于 naive（0.03681 > 0.03674）
3. **HW 和 auto_ar 高度同质**：两者相关性极高，集成增益有限
4. **集成 vs naive 增益稳定**：9 个外部数据集全部为正（+7.7% ~ +25.9%），说明框架正确
5. **性能充裕**：回测 12.88s（500 行），远低于 120s 上限

---

## 时间分配

```
T+0:00 ~ T+0:05   Phase 0: 基础分保障（GitHub + 部署确认）
T+0:05 ~ T+0:30   Phase 1: 精度优化（见下方详细方案）
T+0:30 ~ T+0:45   Phase 2: 冻结 + 回归测试（必须跑 evaluation 脚本对比）
T+0:45 ~ T+0:55   Phase 3: 最终部署 + 推送
T+0:55 ~ T+1:00   Phase 4: 最终验证
```

---

## Phase 0: 基础分保障（5 min）⬅ 最高优先级

- [ ] **0.1** `git push` 最新代码 → 浏览器确认 GitHub 仓库公开可见
- [ ] **0.2** 访问 `gfm156.com/predictor` → 确认页面加载正常
- [ ] **0.3** 上传 `dataset.xlsx` → 一步预测出现 → 回测完成 → xlsx 可下载

---

## Phase 1: 精度优化（25 min）⬅ 核心拿分

> 根据报告数据，重新排列优先级。核心思路：
> - 削弱不稳定的 XGBoost 权重
> - 增强 auto_ar 的基底能力
> - 增加真正有差异化的新模型（而非同质的 HW/AR 微调）
> - 每完成一项跑 evaluation 脚本对比，精度下降立即回退

### ★★★ 1A. 调整集成权重 + XGBoost 降权（3 min）

**原因**：报告明确显示 XGBoost 是最弱且最不稳定的模型，当前权重 0.30 过高。

```python
# 当前
_ENSEMBLE_WEIGHTS = {"holt_winters": 0.35, "arima": 0.35, "xgboost": 0.30}

# 改为：大幅提升 auto_ar 权重，降低 XGBoost
_ENSEMBLE_WEIGHTS = {"holt_winters": 0.25, "arima": 0.50, "xgboost": 0.25}
```

**预期**：auto_ar 在 sample 上 RMSE 最低（0.004118），提高其权重 → ensemble RMSE 应下降  
**风险**：极低（仅改 3 个数字，一行代码）  
**验证**：跑 evaluation 脚本对比 RMSE

### ★★★ 1B. 增强 XGBoost 特征 + 正则化（8 min）

**原因**：XGBoost 不稳定的根源是特征不足 + 过拟合。在 byd 上劣于 naive 说明严重过拟合。

新增特征（针对 log-close price 特征量身定制）：

```python
# 新增特征：
rolling_mean(20)          # 20 期均线
ewm(span=10)              # 指数加权均值（近期加权）
ewm(span=20)              # 慢速指数加权均值
momentum = y[-1] - y[-5]  # 5 期动量差值
momentum10 = y[-1] - y[-10]
log_return = log(y[-1]/y[-2])  # 对数收益率
```

超参调整（加强正则化防过拟合）：

```python
model = xgb.XGBRegressor(
    n_estimators=150,       # 200 → 150（减少避免过拟合）
    max_depth=3,            # 4 → 3（更浅的树）
    learning_rate=0.05,
    subsample=0.7,          # 0.8 → 0.7
    colsample_bytree=0.7,   # 0.8 → 0.7
    reg_alpha=0.5,          # 新增 L1 正则
    reg_lambda=2.0,         # 新增 L2 正则
    min_child_weight=5,     # 新增
    random_state=42,
)
```

**预期**：XGBoost 更保守，减少过拟合 → 外部鲁棒性提升  
**风险**：低  
**验证**：跑 evaluation 脚本，特别关注 byd / mix_growth 外部数据

### ★★☆ 1C. ETS 自动配置选择（5 min）

**原因**：当前 HW 固定 `trend="add", damped_trend=True`，但不同数据可能适合不同配置。

```python
_ETS_CONFIGS = [
    {"trend": "add", "damped_trend": True},
    {"trend": "add", "damped_trend": False},
    {"trend": None, "damped_trend": False},   # SES（简单指数平滑）
]
# 每个配置 fit → 取 AIC 最低的
```

注意：不加 `trend="mul"` 因为 log-close 数据值域在 1.3~1.4，乘法趋势无意义。

**预期**：某些数据段 SES 可能优于 damped trend → 小幅改善  
**风险**：低（外层 try-except 已有）  
**验证**：跑 evaluation 脚本

### ★★☆ 1D. 增加 ARIMA 阶数搜索范围（4 min）

**原因**：auto_ar 已是最强模型，但当前 `max_order = min(5, max(1, series.size // 10))` 限制了搜索空间。对 500 行数据 max_order=5，可能不够。

```python
# 当前
max_order = min(5, max(1, series.size // 10))

# 改为：允许更高阶（数据充足时）
max_order = min(8, max(1, series.size // 8))

# 同时增加差分阶数搜索
for differencing in (0, 1, 2):  # 当前只搜 0, 1
```

**预期**：更大搜索空间找到更优 AR 阶 → auto_ar 精度进一步提升  
**风险**：极低（仅扩大搜索范围）  
**验证**：跑 evaluation 脚本

### ★☆☆ 1E. 添加 LightGBM 第四模型（5 min）— 仅时间充裕时

**原因**：增加集成多样性。但报告显示 tree-based 模型（XGBoost）在该类数据上并非最优，LightGBM 可能有类似问题。

**判断**：仅在 1A-1D 完成且 evaluation 结果正向时才考虑。若 1B 的 XGBoost 改进后仍不稳定，应**跳过** 1E。

**风险**：需加依赖 → 部署可能出问题 → 时间紧张时直接跳过

---

## Phase 1 执行顺序（数据驱动决策）

```
1A（3 min）→ 跑 evaluation → 确认改善 ✓
  ↓
1D（4 min）→ 跑 evaluation → 确认改善 ✓
  ↓
1B（8 min）→ 跑 evaluation → 确认改善 ✓
  ↓
1C（5 min）→ 跑 evaluation → 确认改善 ✓
  ↓
（若有余力）1E（5 min）→ 跑 evaluation → 确认改善 ✓
```

**每一步的铁律**：跑 evaluation 脚本对比下表。任何一项精度下降 → `git checkout -- core/predictor.py` 回退该步改动。

| 指标 | 优化前基线 | 优化后目标 |
|------|-----------|-----------|
| ensemble RMSE | 0.004135 | < 0.004100 |
| ensemble MAE | 0.003262 | < 0.003200 |
| ensemble MAPE | 0.2398% | < 0.2350% |

---

## Phase 2: 冻结 + 回归测试（15 min）

> ⚠ T+30 后禁止新增功能

- [ ] **2.1** 完整 evaluation 脚本最终一跑
  ```bash
  python tests/run_module_b_evaluation.py --report-path report/module_b_evaluation_final.md
  ```
  对比 `report/module_b_evaluation.md`（优化前）和 `report/module_b_evaluation_final.md`（优化后），确认全面改善
- [ ] **2.2** Streamlit 端到端测试
  - 上传 `dataset.xlsx` → 一步预测 → 回测 → 下载 xlsx
  - 打开下载的 xlsx → 确认列名（`date`, `y`）、行数（100 行 = 500 × 0.2）
- [ ] **2.3** 边界测试
  - 只有 `y` 列（无 `date`）→ 应正常
  - 短序列（10 行）→ 应降级到 naive/HW 而非崩溃
- [ ] **2.4** 性能检查
  - 回测总时长仍 < 30s？（当前 12.88s，特征增加后预计 15-20s）
  - 若 > 60s → 减少 XGBoost n_estimators

---

## Phase 3: 最终部署 + 推送（10 min）

- [ ] **3.1** Git 提交 + 推送到 GitHub
  ```bash
  git add -A
  git commit -m "optimize: data-driven ensemble tuning based on evaluation report"
  git push origin main
  ```
  确认仓库：https://github.com/rikka314/predictor
- [ ] **3.2** 同步到服务器（一键完成上传 + 重启）
  ```bash
  bash deploy/sync.sh
  ```
  > 脚本会自动 scp 文件到 `/opt/predictor` 并 `systemctl restart predictor`。
  > SSH 别名 `predictor` 已配置（~/.ssh/config → 115.191.68.122）。
- [ ] **3.3** 若 sync.sh 失败，手动操作
  ```bash
  scp app.py requirements.txt predictor:/opt/predictor/
  scp core/*.py predictor:/opt/predictor/core/
  scp ui/*.py predictor:/opt/predictor/ui/
  scp .streamlit/config.toml predictor:/opt/predictor/.streamlit/
  ssh predictor "systemctl restart predictor"
  ```

---

## Phase 4: 最终验证（5 min）

- [ ] **4.1** 浏览器 `gfm156.com/predictor` → 上传 → 全流程无报错
- [ ] **4.2** GitHub 仓库 https://github.com/rikka314/predictor → 最新提交可见
- [ ] **4.3** 下载 xlsx → 打开确认格式正确

---

## 紧急回退方案

```bash
# 任何时候出问题，一键回退 predictor.py
git checkout -- core/predictor.py
# 或回退所有改动
git stash
```

**核心原则：宁可不优化精度，也不能丢掉基础 70 分。**

---

## 与上一版计划的核心差异

| 维度 | v1（拍脑袋） | v2（数据驱动） |
|------|-------------|---------------|
| XGBoost 策略 | 加更多特征 + 更深树 | **降权 + 加正则化防过拟合** |
| 优先级最高 | 特征工程 | **调权重（1A）+ 扩 ARIMA 搜索（1D）** |
| ETS 配置 | 加 mul 趋势 | **去掉 mul（log 域无意义）** |
| LightGBM | 中优先级 | **降为最低优先级（tree 方法本身不适合）** |
| 自适应权重 | 要做 | **取消（复杂度高，增益有限，不如固定调优）** |
| 验证方式 | 端到端 | **每步跑 evaluation 脚本 + 精度对比表** |

---

## Checklist 总表

### 基础分保障（70 分）
- [ ] GitHub 公开可访问（20 分）
- [ ] WebApp 在线可用（20 分）
- [ ] 上传即触发一步预测（10 分）
- [ ] 回测正确执行（10 分）
- [ ] 输出 xlsx 格式正确（10 分）

### 精度优化（30 分）
- [x] 1A: 调整集成权重（最终 `holt_winters=0.05`, `auto_ar=0.75`, `xgboost=0.20`）
- [x] 1D: 扩大 ARIMA 搜索范围
- [x] 1B: XGBoost 特征增强 + 正则化已实测，sample RMSE 退化至 0.005904，按铁律回退
- [x] 1C: ETS 自动配置选择
- [x] （可选）1E: LightGBM 跳过（新增依赖风险高，tree 模型外部鲁棒性不足）

### 回归验证
- [x] evaluation 脚本跑完对比（`report/module_b_evaluation_final.md`：RMSE 0.004106, MAE 0.003240, MAPE 0.2382%）
- [ ] 端到端 Streamlit 测试通过
- [ ] 部署后线上验证通过
