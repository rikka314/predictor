# Frontend Style Standard（Predict 项目）

> 基于 `stratagy` 项目规范抽取并适配  
> 状态：当前项目前端统一风格基线  
> 适用范围：`/predict` 页面与后续扩展子页面

## 1. 目标

Predict 项目采用“产品页式工具界面”，避免堆叠式后台面板风格：

- 暖白、米白背景，不用整页网格纹理
- 页面重心聚焦在单个主操作区（上传 + 预测）
- 少量必要 surface，不做卡片墙
- 状态提示尽量轻量化（普通文字 + 轻分隔）

## 2. 页面语法

默认结构：

`light header -> intro -> single action surface -> result showcase -> supporting text`

- `light header`：轻量标题与路径提示
- `single action surface`：上传文件、阈值设置、触发预测
- `result showcase`：结果表格、下载按钮、关键指标

## 3. 视觉系统

### 3.1 Token 方向

必须优先使用语义 token，不散落硬编码颜色：

- 背景：`bg-canvas`、`bg-glow`
- Surface：`surface-main`、`surface-sheet`
- 文本：`text-strong`、`text-primary`、`text-muted`
- 强调：`accent-primary`、`accent-warm`
- 状态：`accent-positive`、`accent-warning`、`accent-danger`

### 3.2 Surface 规则

- 页面只保留一个主要操作区和一个主要展示区
- 展示区内部可有轻量 sheet，但排布必须稳定
- 主要靠留白和排版分层，不靠重边框堆层级

## 4. 交互与状态规则

- 主 CTA 可以强调，但不要做成“后台系统按钮”
- 加载、空态、错误必须有清晰文案
- 普通说明优先 `caption` / 普通文字，不滥用大提示框
- 行布局（如文本 + 小按钮）必须检查垂直对齐

## 5. HTML/CSS 实施细则

- 大块 HTML 建议走共享渲染封装（后续可在 `ui/theme.py` 统一）
- 页面文件负责内容结构，不再复制第二套颜色/圆角/间距系统
- 新增站点级样式优先沉淀到 `ui/theme.py`

## 6. 反模式

- 满屏大卡片/大边框/大面板
- 顶部做成厚重导航盒
- 依赖绝对定位制造复杂重叠层级
- 普通说明全部塞进提示框
- 页面文件里再次定义独立视觉系统

## 7. 完成标准

- 页面第一眼像产品工具页，不像实验面板
- 操作重心明确，展示重心明确
- 上传、预测、结果查看、下载四步路径清晰
- 桌面与窄屏均无控件重叠和按钮挤压
