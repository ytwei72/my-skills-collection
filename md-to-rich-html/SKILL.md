---
name: md-to-rich-html
description: >-
  Converts documents (Markdown and other text-friendly formats) into one
  self-contained HTML file with responsive layout, theme-aware colors, and
  inline SVG diagrams inferred from content. Supports user-specified source
  format lists (e.g. md, txt, docx). Use when converting MD/TXT/HTML/CSV/JSON
  to HTML, batch-exporting listed formats to a web page, or when the user asks
  for 网页 / 网页版 / static HTML / single-file HTML output.
disable-model-invocation: false
---

# 文档 → 富表现 HTML（多源格式）

> 本 skill 为项目**默认可自动发现**的 skill 之一；其余 `.cursor/skills/` 下的 skill 须用户明确点名后才加载（见 `.cursor/rules/skills-lazy-load.mdc`）。

## 何时使用

- 用户要把 **`.md`、`.txt`、`.html` 片段、`.csv`、`.json`** 等转成 **单文件 `.html`**，或「导出网页 / 静态页 / 离线可打开」。
- 用户给出 **若干种后缀/格式列表**（例如「把 md、txt、docx 都转成 html」）：对列表中**每一种**分别处理；未提供输出路径时，**与源文件同目录、同名改 `.html`**。
- 用户明确要 **HTML、网页、web、单文件 HTML** 时，优先按本技能产出，而不是只给未样式化的 HTML 片段。

## 产出物约束

- **单文件**：一个 `.html`，内联 `<style>`；图表用 **内联 SVG**（或极少量的 `data:`），避免外链字体/脚本/CDN（除非用户要求）。
- **可读与可维护**：语义化标签（`header` / `main` / `section` / `article` / `nav` / `footer`）；源为 Markdown 时标题层级与 MD 对应；其他格式按解析结果映射到合理标题结构。
- **多端自适应**：`viewport`；用 `clamp()`、`max-width`、CSS Grid/Flex、`min()`；窄屏下多列改单列；大图 `overflow-x: auto`。
- **配色**：`color-scheme: light dark` + `:root` CSS 变量（背景、表面、正文、弱化、主色、强调色、边框）；深浅色对比达标，正文对比度优先于装饰。
- **无障碍**：图表配 `<title>` / `<desc>` 或 `aria-labelledby`；对比条等用 `aria-label`；勿仅用颜色传达唯一信息。

## 支持的源格式（按扩展名分支）

| 扩展名 | 处理策略 |
|--------|----------|
| `.md` / `.markdown` | 主路径：按完整流程解析 MD 语义。 |
| `.txt` | 按空行分段；可识别 `一、二、`、`1.`、`#` 行首等弱结构；无结构则单篇 `article` + 段落。 |
| `.html` / `.htm` | 若已是整页：可套统一主题壳或按用户要求只美化局部；若是片段：包进标准单页模板并补 `meta`/样式。 |
| `.csv` | 首行表头 → `<table>`；可加简短 `header` 说明文件名或用户标题；大表横向滚动容器。 |
| `.json` | 对象/数组 → 定义列表、卡片或折叠 `details`；避免把整个大 JSON 无样式 dump；敏感字段可打码（若用户要求）。 |
| `.docx` / `.rtf` / `.odt` | **优先**：若环境或仓库中有 **Pandoc** / 现成转换脚本，先转为 MD 或 HTML 再套本技能版式；**若无工具**：告知限制，请用户导出 `.md`/`.html` 或提供可复制正文，再生成富 HTML。 |
| `.org` / `.rst` / `.adoc` | 有 Pandoc 则用 `pandoc` 转 MD/HTML 中间稿再版式化；否则读纯文本按 `.txt` 降级。 |

用户说「和 Word 里内容一样」但只有 `.docx`：不要凭空编造正文；**必须先有可读文本**（转换或用户粘贴）。

## 工作流程

1. **识别输入**：扩展名 + 用户是否给出「格式列表」或一批路径；多文件则**逐文件**重复下列步骤。
2. **归一化为内容模型**：得到「标题树 + 块级元素（段落/列表/代码/表）+ 强调」；非 MD 源在内部可当「准 MD」处理。
3. **识别可图形化内容**：流程、架构、对比、分层、闭环、时间线、占比等（与源格式无关，看语义）。
4. **定信息架构**：封面式 `header`（可选）+ 按 `h1/h2` 分 `section`；长文考虑页内锚点或目录块。
5. **写 HTML 骨架**：先结构后装饰；代码用 `<code>` / `<pre>`；表格用 `<table>` + `overflow-x` 容器。
6. **加样式**：统一圆角、阴影、间距刻度；全篇一致。
7. **按需生成图表**（内联 SVG，见下节启发式）。
8. **自检**：`viewBox`、文字与曲线分离、`hero` 内颜色不被全局样式覆盖。

## 批量 / 指定格式列表

- 用户写「把 **md、txt、csv** 转成 html」：对仓库中**本次任务涉及的每个匹配文件**各生成一个 `.html`（或用户指定的输出目录）。
- 用户写「**只转**这些路径」：严格按路径列表，不擅自扩大范围。
- 某一格式在当前环境**无法可靠读取**（如二进制且无转换器）：**跳过该文件并说明原因**，不生成空壳冒充内容。

## 图表启发式（按内容选型）

| 内容信号 | 建议形式 |
|---------|---------|
| 前后/人工 vs 自动、A/B | 并排对比卡 + 中间箭头 |
| 步骤链、pipeline、从 A 到 B | 横向流程图（框 + 箭头）；步骤多则纵向 |
| 远程/本地/回执闭环 | 左中右或上下分区 + 虚线表示回传 |
| 分层、信任边界、职责划分 | 纵向三层条带 或 左右双区；安全域可用同心椭圆 + **环带异色/虚线实线区分** |
| 三类并列收益/痛点 | 三列卡片（窄屏一列）+ 小图标 |
| 关键词枚举 | pill / tag 行 |
| 数据表（小） | HTML `<table>` + 斑马纹 |
| 时间线 | 竖线 + 节点 + 日期标签 |

**原则**：一图一事；能用一个简单 SVG 说清就不堆叠；文字标签放在图形**安全区**（独立 caption 区、圆角底条、或 `viewBox` 扩高），避免与路径/椭圆重叠。

## 样式基线（可微调，全篇一致）

- 字体栈：系统 UI + `PingFang SC` / `Microsoft YaHei`。
- 主色与源文档品牌无关时，沿用项目常见 **青绿 + 暖橙点缀** 或用户指定色。
- `header.hero` 上的副标题：显式设置 `color`（如白或近白），避免被全局段落颜色覆盖。

## 交付

- 默认写入用户给定路径或与**源文件**同目录、**同名改 `.html`**（若用户未指定）。
- 多文件批量时：列出每个输出路径；若部分失败，单独标明原因。
- 简要说明在浏览器中打开即可，无需冗长复述。

## 参考实现

本仓库中可参考的成品：`ReportsDoc/财务日常提效/财务日常工作的优化提效汇报.html`（布局、深浅色、SVG、移动端与 `viewBox` 处理）。

## 延伸阅读

图表类型与版式清单的扩充版见 [reference.md](reference.md)（按需打开，避免占满上下文）。
