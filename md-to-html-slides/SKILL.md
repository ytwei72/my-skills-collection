---
name: md-to-html-slides
description: >-
  把 Markdown 文档转成单文件 HTML 翻页演示稿（仿 Reveal.js / Slidev 但极简自写、零外链）。
  默认内置 3 主题（青蓝/晴空/雅紫）可运行时切换；支持指令关闭主题或锁定某一主题。
  仅在用户明确点名本 skill（/md-to-html-slides、使用 md-to-html-slides 等）时加载。
  未点名时不要读取本技能。
disable-model-invocation: true
---

# Markdown → HTML 翻页演示稿（单文件 .slides.html）

## 何时使用

- 用户要把 `.md` / `.markdown` 转成「演示稿 / PPT / 幻灯片 / slides / web 版 PPT」，且没明确要求必须是 `.pptx`。
- 用户要一份**双击即放映**的离线单文件，能 Ctrl+P 直接打印 PDF。
- 用户希望比 `md-to-rich-html` 更"分页可演示"的效果，但又不想走 `ppt-master` 那套重流程。

> 与其他 skill 的边界：
> - `md-to-rich-html`：长滚动单页富文本网页，不分页、不放映。
> - `md-to-agent-response-html`：摘要卡 + 详情双页，不演示。
> - `ppt-master`（rule：`.cursor/rules/ppt-master.mdc`）：**真 .pptx**、原生 DrawingML 形状、可在 PowerPoint 里编辑、有动画/配音/模板体系。**用户明确说要 .pptx、要在 PowerPoint 里改、要原生动画**时优先用 ppt-master，不要用本 skill。
> - 用户说「做 PPT」但意图模糊时，**先问一句**：要 `.pptx` 文件还是 HTML 演示稿（浏览器放映 + 可打 PDF）？

## 输入约束

- **仅支持** `.md` / `.markdown`。其他扩展名一律拒绝，提示用户先转成 MD 或改用 `md-to-rich-html`。
- 单文件 → 一份 deck；多文件 → 按用户给的顺序拼成同一份 deck，每个 md 自动加章节分隔页（章节名取自文件名，去扩展名）。
- 目录路径 → 扫描目录下所有 .md，按字典序合并；超过 5 个文件先和用户确认顺序。

## 产出物

- **单文件** `<源文件名>.slides.html`，与源文件同目录（用户未指定输出路径时）。
- 完全离线、无 CDN、无外部字体、无外部 JS；图片转 base64 内联（>500KB 单张图给警告但不阻断）。
- 浏览器双击直接放映；网络/U 盘传给别人也能用。

## 必须遵守的 HTML 骨架契约（关键！）

> 这套骨架既保证**当下放映体验**，又为**未来转真 .pptx 的 toolkit**预留接口。所有用本 skill 生成的 HTML **必须**满足以下 5 条，不得自由发挥：

1. **结构类名固定**（截图/解析脚本依赖这些 hook）：
   ```html
   <main class="deck" data-format="169">
     <section class="slide" data-index="0" data-layout="cover">
       <!-- 内容 -->
       <aside class="notes">演讲者备注…</aside>
     </section>
     <section class="slide" data-index="1" data-layout="content">…</section>
     …
   </main>
   ```
   - 容器：`<main class="deck">`，`data-format="169"|"43"`。
   - 每页：`<section class="slide" data-index="N" data-layout="...">`，`N` 从 0 开始连续。
   - 演讲者备注：每页内一个 `<aside class="notes">`（默认隐藏，按 S 显示）。

2. **必须挂全局 JS API** `window.deckAPI`：
   ```js
   window.deckAPI = {
     slideCount: <number>,           // 总页数
     goToSlide: (i) => void,         // 跳到第 i 页（0-based），并使其 .active
     getNotes:  (i) => string,       // 返回第 i 页备注 textContent
     getCurrent: () => number,       // 当前页索引
   };
   ```

3. **必须支持 `?export=1` 导出模式**：当 URL 含此查询参数时：
   - 强制关闭所有 CSS `transition` / `animation`（注入 `* { transition:none !important; animation:none !important; }`）。
   - 隐藏控制条 `nav.ctrl`、键位提示 `.toast`、鼠标光标 (`body { cursor:none !important }`)。
   - 强制单页可见 + 全画布尺寸，方便无头浏览器逐页截图。

4. **字体只用系统 UI 栈**，禁用 webfont（保证截图/打印无网时也对得上）：
   ```css
   font-family: -apple-system, BlinkMacSystemFont, "PingFang SC",
                "Microsoft YaHei", "Segoe UI", system-ui, sans-serif;
   ```

5. **打印样式必须正确**：每页 `page-break-after: always`；隐藏控制条；强制白底黑字（除非用户要求保留深色）；`@page { size: 1280px 720px; margin: 0 }`（按当前画布尺寸）。

> 完整可复用的 HTML/CSS/JS 骨架与各 layout 样例见 [reference.md](reference.md)。

## 画布与比例

- 默认 **16:9**，逻辑像素 **1920×1080**（高清、字号更从容、投屏更锐利）；CSS 变量 `--slide-w / --slide-h` 控制。
- 用户说「4:3 / 老比例 / 投影仪用」→ 切 **4:3**，**1440×1080**，`data-format="43"`（与 16:9 等高，组件/字号无需重调）。
- 不论比例，整个 `.deck` 通过 `transform: scale(...)` 自适应窗口（`fit: contain`），永远完整居中显示，不被裁切。
- 旧版曾用 1280×720，已弃用——画布偏小会逼出小字号、版面拥挤；新产物一律 1920×1080。

## 版面质量硬标准（不达标即返工）

> **质量基准线**：本 skill 生成的 deck，视觉效果与可用度**不得低于**项目内样板
> `PlatformSystem/AiBusinessAssistant/ai-product-catalog-slides-v1.html`。
> 下列硬标准均从该样板的多轮打磨中提炼，**逐条都要满足**，对应代码见 [reference.md](reference.md) §高质量组件库 / §多主题 / §版面填充与安全区。

1. **字号下限（@1920×1080，从读者角度，宁大勿小）**：
   - 正文 / 要点 / 列表 ≥ **20px**；表格 ≥ **22px**；卡片描述 ≥ **20px**；卡片标题 ≥ **26px**。
   - 页面主标题 **48–56px**；副标题 **24–28px**；大数字 / KPI **40–52px**。
   - 任何"框内 / 条内 / 角标说明"文字 ≥ **18px**。**禁止出现 < 16px 的正文级文字**（仅页码角标可更小）。
   - 4:3 同此（等高画布）。如内容放不下，**先切页或精简，绝不靠缩字硬塞**。

2. **垂直填充、杜绝"头重脚轻"**：
   - 每页正文容器用 flex 纵向布局：内容少 → `justify-content:center`（整体居中）；内容多 → `space-between`（撑满）。
   - 内容须占版心 **≥ 75% 高度**，**严禁内容堆在上半屏、下半屏大片留白**。
   - 内容偏少时优先「**结合本页主题适度延展 + 换更丰富的表现形式**」，其次才是居中留白；不得灌水编造。

3. **表现形式多样化（反单调）**：
   - 一份 deck **至少使用 4 种**不同呈现形式，不许通篇"标题 + 圆点列表"。
   - 备选（见 reference.md §高质量组件库）：卡片网格 / KPI 数字条 / **前后对比条** / 图标清单 / **架构分层图** / **流程箭头图** / 时间轴 / 路径步骤 / 痛点·方案双栏 / 标签云 / 强调框 / 统计条。

4. **底部安全区，控制条不挡内容**：
   - 正文容器底部预留 **≥ 96px** 安全区；固定控制条 `nav.ctrl` 保持紧凑，**不得遮盖任何页面内容**（这是样板里踩过的坑）。

5. **对比条 / 进度条文字必须独立可读**：
   - 数值标签放在条**内左侧、深色大字（≥18px）**；**不得**把文字塞进彩色填充里随条宽被压小或裁切。

6. **密度平衡**：单页要点 ≤ 6 条、卡片 ≤ 6 张、表格 ≤ 8 行；超出切页。既不灌水，也不留大白。

7. **图示优先**：凡 MD 含"架构 / 分层 / 流程 / 步骤 / 前后对比 / 时间线 / 占比"语义，**优先画图**（CSS 框图或内联 SVG），而非纯文字罗列。

## 可选模板（templates/ppt-layouts/）

本仓库自带 3 套视觉模板（路径：`templates/ppt-layouts/`）：

| 名称 | 风格 | 何时建议 |
|---|---|---|
| `dark_tech` | 深色科技、青蓝主色 | 技术分享、产品发布 |
| `minimal_business` | 极简商务、暖灰白底 | 内部汇报、提案 |
| `modern_academic` | 现代学术、稳重蓝 | 学术汇报、培训 |

使用规则：
- **用户明确点名**模板（"用 dark_tech 模板" / "走深色科技风"）→ 读 `templates/ppt-layouts/<name>/design_spec.md`，取出主色 / 字体 / 装饰元素，**作为 CSS 变量与封面/章节装饰的灵感来源**（不需要拷贝 SVG，模型按 spec 的色彩与几何意图自己重画 CSS+SVG）。
- 用户没点名 → 不主动提模板，根据 MD 内容氛围自定一套主题色（`md-to-rich-html` 的"青绿 + 暖橙"基线）。
- 详细模板挑选指南在 [reference.md](reference.md) §模板。

### 多主题（默认开启，可指令覆盖）

**默认行为**：内置 **3 套清新配色**并支持运行时切换——**青蓝（`aqua`）/ 晴空（`azure`）/ 雅紫（`violet`）**（取自质量样板）。实现：` <html data-theme="aqua">` + `[data-theme="..."]` CSS 变量；控制条「◐」按钮 + 键盘 **T** 循环切换；选择记忆到 `localStorage`。详见 [reference.md](reference.md) §多主题与切换器。

**用户指令解析**（按优先级，命中即生效）：

| 用户说法 | 行为 |
|---|---|
| （未提及主题） | **默认**：3 主题 + 切换器 + 默认 `aqua` |
| 「关闭主题 / 不要主题切换 / 单一配色 / 固定配色 / 不要换肤」 | **单主题模式**：仅保留一套配色，**去掉**切换器按钮、`T` 键、`cycleTheme`；默认 `aqua` |
| 「指定主题：青蓝 / 用 aqua 主题 / 默认晴空 / 雅紫配色」 | **锁定单主题**：只输出指定主题，去掉切换器；`<html data-theme="...">` 设为对应 id |
| 「3 主题但默认晴空 / 多主题，起始用 violet」 | **多主题 + 自定义默认**：保留切换器，初始 `data-theme` 与 `localStorage` 种子设为指定主题 |
| 「深色 / 深色科技 / 用 dark_tech」 | 走 `templates/ppt-layouts/dark_tech` 或深色变量集；若未说「不要切换」仍保留 3 主题切换（除非与 dark 模板冲突，则以模板为准并单主题） |

主题 id 对照：`aqua`=青蓝、`azure`=晴空、`violet`=雅紫。用户说中文名或 id 均可。

`prefers-color-scheme` 仅作**未启用多主题切换**时的兜底；多主题模式下以 `data-theme` 为准。

## MD → 幻灯片切片规则

| MD 元素 | 映射 |
|---|---|
| `# 一级标题`（首个） | **封面页**（cover）：大标题 + 可选副标题（取首段引述/导语） |
| `# 一级标题`（后续） | **章节分隔页**（section）：章节序号 + 章节名，整页留白 |
| `## 二级标题` | **新建一页内容页**（content）：标题 + 该 `##` 之下的所有正文 |
| `### 三级标题` | 内容页内的子标题，不切页（除非该 `##` 之下有 ≥3 个 `###` 且各自正文较多，则按 `###` 切页） |
| 列表（`-` / `1.`） | 居中要点列表，每条带圆点/数字，最多 6 条/页；超出自动切下一页 |
| 表格 | 居中表格 layout，最多 8 行/页，超出切下一页或缩字号 |
| 代码块 | 居中代码 layout，等宽字体；行数 >12 时切多页 |
| 引用块 `>` | 大字号引用 layout（金句页） |
| 图片 ![]() | image-and-text layout（半图半文）或独占一页 image-only |
| `<!-- notes: ... -->` HTML 注释 | 写入当前页 `<aside class="notes">` |
| `> 备注：…` 引用块 | 也写入当前页备注（与上者并列，二选一即可） |
| `---` 分隔线 | **强制切页**（用户手动断页） |

**末页**：自动加一页 ending（"Q & A" / "Thank You"）；用户 MD 末尾已有 `## 致谢` / `## 总结` / `## Q&A` 时不重复。

**页数控制**：默认目标 10~25 页；MD 太长（>40 页）时给提示并询问是否压缩。

## 演讲者备注（按优先级取）

1. 显式 `<!-- notes: ... -->` HTML 注释（贴在该页内容紧邻处）
2. `> 备注：…` 引用块（贴在该页内容紧邻处）
3. 自动生成（默认开启）：模型基于该页内容生成 1~3 句口述提示；**不准编造原文没有的事实**，只做"如何讲这一页"的引导

按 S 切换演讲者视图（侧边栏显示备注，主区显示当前页 + 下一页缩略图 + 计时器）。

## 图表（无外部依赖）

完全沿用 `md-to-rich-html` 的图表启发式（流程/对比/分层/时间线/占比）：

- MD 里有具体数字 → 内联 SVG 画简单条形/比例条（注明"示意"）
- MD 描述的是结构（流程/分层/对比） → 内联 SVG 画框图箭头
- MD 没有可图形化语义 → 不画，避免装饰性凑数
- 复杂的 mermaid / plantuml：转成等价的内联 SVG 框图；不内嵌 mermaid.js（违反"零外链"）

## 交互

| 操作 | 行为 |
|---|---|
| ← / PgUp / Backspace | 上一页 |
| → / PgDn / Space / Enter | 下一页 |
| Home / End | 首/末页 |
| 数字键 + Enter | 跳转到该页（如 `7` `Enter`） |
| F | 全屏切换 |
| O | 缩略图概览（再按 O 退出；点缩略图跳转） |
| S | 演讲者视图切换 |
| T | 切换配色主题（青蓝 / 晴空 / 雅紫，循环；**单主题模式时无此键**） |
| B | 黑屏（讲者注意力收回） |
| ? | 快捷键提示浮层 |
| Ctrl/⌘ + P | 浏览器打印为 PDF（每页一张） |
| 鼠标 | 右下角浮一组迷你按钮：← · 当前/总 · → · 全屏 · 概览 · 备注 |
| 触屏 | 左/右滑翻页；上滑显示概览 |

## 配色与无障碍

- `:root` CSS 变量：`--bg / --surface / --text / --muted / --primary / --accent / --border / --shadow`，深浅色用 `@media (prefers-color-scheme)` 切换。
- 对比度：正文 ≥ 4.5:1，标题 ≥ 3:1。
- 控制条 `aria-label`、备注 `<aside aria-label="演讲者备注">`、概览缩略图 `aria-label="第 N 页"`。
- 不仅靠颜色传达信息（图表配文字标签）。

## 工作流程

1. **校验输入**：必须是 `.md` / `.markdown`；多文件记录顺序；非 md 拒绝。
2. **解析归一化**：MD → 标题树 + 块级元素 + 强调；同时抽取每页的 notes、强制断页符 `---`。
3. **切页**：按上节"切片规则"切成 slides 数组，每页定 layout。
4. **写 HTML**：套用 [reference.md](reference.md) 的骨架，注入 CSS 变量、JS、各页 `<section>`。务必满足"骨架契约 5 条"。
5. **本地自检**（写完后心算一遍）：
   - **结构契约**：`<main class="deck">` 包 N 个 `<section class="slide" data-index="0..N-1" data-layout="...">`
   - JS 必有 `window.deckAPI = {slideCount, goToSlide, getNotes, getCurrent}`
   - 字符串 `?export=1` 必出现在 JS 里且对应行为正确
   - 字体栈不含 `Google Fonts` / `@import url(http`（系统栈，离线可用）
   - `@media print` 段落存在，含 `page-break-after: always`
   - 备注按 S 可切换显示
   - 整 deck 用 `transform: scale()` 自适应窗口
   - 16:9 → `--slide-w: 1920px; --slide-h: 1080px`；4:3 → `1440px / 1080px`
   - **多主题**：默认 3 套 + 按钮/键 T + localStorage；用户指令「关闭主题」时无切换器；「指定某主题」时锁定该 `data-theme`
   - —— 以下为「版面质量硬标准」自检（逐条过）——
   - 字号达标：正文 ≥20px、表格 ≥22px、卡片标题 ≥26px、主标题 48–56px；无 <16px 正文级文字
   - 垂直填充：每页内容占版心 ≥75% 高度，无"头重脚轻 / 下半屏大白"
   - 表现形式 ≥4 种，未通篇圆点列表
   - 底部 ≥96px 安全区，控制条不挡内容
   - 对比条文字独立、深色、≥18px、不裁切
   - 有架构 / 流程 / 对比 / 时间线语义处已出图，而非纯文字
6. **交付**：告知文件路径 + 一句话操作提示（"双击打开，← / → 翻页，F 全屏，Ctrl+P 打印 PDF"）。

## 为未来转 .pptx 预留的钩子（已包含在骨架契约里）

后续会有独立 toolkit `toolkits/html_slides_to_pptx/` 把本 skill 的产物转成真 .pptx（默认走 Playwright 截图模式，保真 100% 但文字不可编辑）。本 skill 只要严守上述"骨架契约 5 条"，转换器就是输入即输出的纯函数，**HTML skill 后续怎么改样式都不影响转换器**。

> 当前阶段不实现转换器；用户问"能不能转 .pptx"时告知：可以后续加 toolkit，目前先用浏览器 Ctrl+P 导 PDF 当过渡。

## 反幻觉与边界

- **不编造数字 / 结论 / 人名 / 日期**：MD 里没有的不要写进幻灯片。
- **不灌水**：MD 内容少时宁可只出 5~6 页，也不要硬撑到 20 页。
- **不二次美化原文**：把 MD 的句子润色为"演示标题"是允许的（短化、动词化），但不能改变事实。
- **敏感信息**（手机号/邮箱/密钥）：演示稿里建议打码，演讲者备注里可保留完整版。

## 拒绝场景

| 用户输入 | 处理 |
|---|---|
| `.docx` / `.txt` / `.html` / `.pdf` 作为源 | 拒绝，提示先转 .md |
| 只给主题（"做一份 AI 趋势 PPT"，无源文档） | 拒绝，提示提供 md 源；或建议走 `ppt-master` 的 topic-research |
| 明确要求"必须是 .pptx 能在 PowerPoint 里编辑" | 走 `ppt-master`（提示用户切换） |
| 单文件 HTML 里同时要"摘要卡入口 + 演示稿" | 拒绝二合一，建议组合 `md-to-agent-response-html` + 本 skill 各跑一次 |

## 交付话术

简洁告知文件路径 + 操作提示，例如：

> 已生成 `Miscellaneous/弈智纠纷/弈智股东纠纷应对指南_v1.1.slides.html`。
> 双击打开即放映，← / → 翻页，F 全屏，O 概览，S 演讲者备注，Ctrl+P 打印 PDF。

不要重复贴大段 HTML 源码给用户，除非他明确要看。

## 版本计划（模板体系演进）

后续版本以**可插拔模板包**组织，而不仅是换色。每版增量应同时考虑四层，并在 [reference.md](reference.md) 与 `templates/ppt-layouts/` 中留痕：

| 层级 | 说明 | 当前状态 | 计划 |
|---|---|---|---|
| **样式（Style）** | 配色变量、字体栈、阴影/圆角/渐变、深色与打印 | ✅ 3 内置主题 + CSS 变量 | 更多主题包；与 `design_spec.md` 自动对齐 |
| **组件（Component）** | 卡片/KPI/对比条/架构图/流程图/时间轴等可复用块 | ✅ reference §高质量组件库 | 组件 catalog + 语义自动选型 |
| **版面（Layout）** | `data-layout` 页型：cover / section / content / two-col … | ✅ 10+ layout | 扩展 stat / timeline layout；MD 映射表自动化 |
| **模板（Template）** | 整 deck 视觉包：`templates/ppt-layouts/<id>/` | ✅ 3 套（dark_tech / minimal_business / modern_academic） | 模板索引 + HTML 侧 design token 导入；与 ppt-master SVG 同源 |

**版本号约定**（写在产出 HTML 注释 `<!-- md-to-html-slides vX.Y -->` 可选）：
- **minor**：新增主题/组件/layout，向后兼容
- **major**：骨架契约或 `deckAPI` 行为变更（需同步 `toolkits/html_slides_to_pptx`）

用户点名「用 xxx 模板」时，读取 `templates/ppt-layouts/<id>/design_spec.md`，将样式层 + 装饰倾向注入 CSS 变量；组件与 layout 仍走本 skill 骨架，不拷贝 SVG 文件。

## 延伸阅读

- 人类使用说明：[README.md](README.md)（触发方式、主题指令、示例）
- 实现细节：[reference.md](reference.md)（骨架、组件库、layout、主题实现）
