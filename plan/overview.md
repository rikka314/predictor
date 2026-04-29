# 项目计划总览（按最新题目资料）

## 目标
将现有占位框架重写为一个时间序列预测 WebApp，满足 AIE1902 final_test 全部评分要求。
本轮已先完成文档与框架对齐；代码实现按后续指令执行。

## 核心决策

| 问题 | 决策 | 理由 |
|------|------|------|
| 预测方法 | 集成：Holt-Winters + Auto-ARIMA + XGBoost-lag | 三者互补，覆盖趋势/季节/非线性 |
| 触发时机 | 上传即自动触发，无需按钮 | 满足评分 (iii) |
| 输出格式 | xlsx，含 `y` + 可选 `date` | 满足评分 (v) |
| 回测方式 | 80/20 时序分割 + 严格滚动逐步预测 | 无数据泄漏 |

## 题目数据快照（dataset.xlsx）

- 首个 sheet：`Sheet1`
- 字段：`date`, `y`
- 数据规模：约 500 条样本

## 文件结构（重写后）

```
app.py                  ← Streamlit 入口
requirements.txt        ← 新增依赖
core/
  config.py             ← 全局配置常量
  io.py                 ← xlsx 读写、数据验证
  predictor.py          ← 预测引擎（集成模型）
ui/
  predict_page.py       ← 主页面逻辑（自动触发）
  theme.py              ← 样式注入
deploy/
  deploy.sh
  nginx_predict.conf
plan/                   ← 本计划文件夹
  overview.md
  module_A_io.md
  module_B_predictor.md
  module_C_ui.md
  module_D_infra.md
```

## 时间线

```
0:00-0:15   Module D   requirements.txt + 结构确认
0:00-0:20   Module A   core/io.py 重写
0:00-1:00   Module B   core/predictor.py（核心，45-60 min）
0:20-0:45   Module C   UI 骨架（依赖 A 接口定义）
0:45-1:15   Module C   UI 图表与下载逻辑
1:00-1:20   集成测试   用 dataset.xlsx 端到端验证
1:20-1:40   调参修复   调整权重、修复边界情况
1:40-2:00   部署提交   推送 GitHub，部署上线
```

## 并行策略
- Module A、B、D 可完全并行启动（互不依赖）
- Module C 依赖 A 的接口签名（约 0:20 后可启动）
- 集成测试依赖所有模块完成
