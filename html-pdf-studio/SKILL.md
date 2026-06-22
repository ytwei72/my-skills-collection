---
name: html-pdf-studio
description: 把 HTML（本地文件或 http(s) URL）转换成 PDF。默认 continuous 连续单页（保留桌面布局、不分页、文本可选）；仅当用户明确要求标准分页/A4/页码/多页打印时才用 paged。另支持页眉页脚、PDF 书签（--bookmarks，优先于目录）、PDF 目录页（--toc）、水印、元数据、加密、合并、脱敏与预览自检。用户说"HTML转PDF""网页转PDF""单页/不分页/长图式PDF"或抱怨导出被分页/裁切时用本技能；用户说"书签/大纲"时加 --bookmarks；用户说"PDF目录/添加目录/更新目录"时加 --toc；禁止因 HTML 有章节/表格/目录就擅自改用 paged。
disable-model-invocation: true
---

# html-pdf-studio

用本机无头 Chrome/Edge（`--print-to-pdf`，零额外运行时依赖）渲染，再用 PyMuPDF
做版面加工。两条职责分离，覆盖从"长滚动网页"到"标准分页文档"的完整 HTML→PDF
需求。

本仓库安装路径：`.cursor/skills/html-pdf-studio/`。

依赖：项目 `.venv` 已安装 `pymupdf`；本机有 Chrome 或 Edge。

> 与 `onepage-pdf` 的关系：本技能是其超集。`onepage-pdf` 只做"连续单页裁切"，
> 本技能在沿用并重写该裁切内核的同时，新增 paged 分页、页眉页脚页码、书签目录、
> 水印、元数据、加密、合并、URL 输入、预览自检等能力。

## Agent 必读：模式选择（硬规则）

**脚本默认 `--mode continuous`。Agent 必须遵守下列规则，不得擅自改用 `paged`。**

### 默认用 continuous

以下任一情况成立时，**一律 `continuous`**（可省略 `--mode`，或显式写
`--mode continuous`）：

- 用户只说「HTML 转 PDF / 导出 PDF / 生成 PDF / 网页转 PDF」，**未指定分页方式**
- 用户要「单页 / 不分页 / 长图式 / 连续页 / 保留网页布局」
- 用户抱怨「被分页了 / 内容被切断 / 布局塌了」
- 源 HTML 来自 `md-to-rich-html`、落地页、提案、培训页、仪表盘等**网页式排版**
- 源 HTML **虽有**章节标题、表格、文内目录、多栏布局——**这些不是选用 paged 的理由**

### 仅当用户明确要求时才用 paged

**只有**用户原话或任务里**明确出现**下列意图之一，才用 `--mode paged`：

- 「A4 / Letter」「标准分页」「多页」「打印版（分页含义）」「分页 PDF」
- 「页码」「第 X 页」「页眉页脚（含页码）」
- 「按纸张打印」「投递 Acrobat / 打印机（且要分页）」

若用户意图模糊（例如只说「报告」但未说要分页），**先问一句是否分页**；用户不
回复则 **默认 continuous**。

### 禁止的推断（常见误用）

| 错误推断 | 正确做法 |
|---|---|
| 「有 h1/h2 章节 → 报告类 → 用 paged」 | 结构不等于分页需求；默认 **continuous** |
| 「有 `<table>` → 文档类 → 用 paged」 | 表格在 continuous 里完整保留；默认 **continuous** |
| 「HTML 里有目录/大纲 → 需要导航 → 用 paged」 | 书签用 **`--bookmarks`**（continuous/paged 均可）；目录页用 **`--toc`**（paged） |
| 「内容很长 → 应该 A4 分页」 | 长内容正是 continuous 的强项；除非用户要分页 |
| 「顺便加页眉页脚更专业 → 用 paged」 | 单页 PDF 一般不加 `{page}/{pages}` 页码；未要求分页则 **continuous** |

### 用户要求「书签 / 大纲 / 侧栏导航」

当用户原话**明确出现**「书签」「加大纲」「侧栏导航」「PDF 大纲」等，且**未要求
目录页**时，加 **`--bookmarks`**（可配合 `--toc-depth`）：

1. **不改正文**：保留 HTML 文内目录（`nav.toc` 等），不插入目录页，页数不变。
2. **仅写阅读器侧栏大纲**：由 HTML `h1..hN` 定位并生成 PDF 书签。
3. **模式不变**：continuous / paged 沿用用户已指定或默认的模式。
4. **优先于 `--toc`**：若两者同时出现，只按书签处理。

```powershell
.venv\Scripts\python.exe .cursor\skills\html-pdf-studio\scripts\html2pdf.py input.html `
    -o output.pdf --width 1280 --bookmarks --toc-depth 3
```

### 用户要求「PDF 目录 / 添加目录 / 更新目录」

当用户原话或任务**明确出现**「PDF 目录」「添加目录」「更新目录」「生成目录页」
等意图时，**必须加 `--toc`**（可配合 `--toc-depth`、`--toc-title`）。**不要**用
`--bookmarks` 代替目录页需求。

1. **剥离 HTML 文内目录**：移除 `nav.toc`、`#toc`、`.table-of-contents` 等块，
   不在 PDF 正文中重复呈现原 HTML 目录。
2. **生成 PDF 格式目录**：
   - **paged 模式**：在文前插入独立目录页（标题 + 层级缩进 + 点引导符 + 页码），
     并同步写入书签大纲。
   - **continuous 模式**：仅剥离 HTML 文内目录并写书签大纲（单页无法做分页目录）。

用户同时要目录页时，通常也意味着需要分页——若尚未明确分页，**先确认是否用
paged**。

```powershell
.venv\Scripts\python.exe .cursor\skills\html-pdf-studio\scripts\html2pdf.py input.html `
    -o output.pdf --mode paged --paper A4 --margin "18 16 20 16" `
    --toc --toc-depth 3 --toc-title "目录"
```

### `--bookmarks` 与 `--toc` 对照（Agent 速查）

| | `--bookmarks` | `--toc` |
|---|---|---|
| 正文 | 不改 | 移除 HTML 文内目录；paged 插入目录页 |
| 侧栏 | 有书签 | 有书签 |
| continuous | ✅ | 仅书签（无目录页） |
| 同时指定 | **书签优先** | 被忽略 |

更多示例见 [README.md](README.md)。

### paged 专属参数不得反向触发 paged

`--paper`、`--landscape`、带 `{page}`/`{pages}` 的 `--footer` 等**仅在与用户
明确要分页时**才使用。用户未要求分页时：

- **不要**传 `--mode paged`
- **不要**传 `--paper` / `--margin`（paged 几何）
- 可加 `--watermark`、`--title`、`--preview`、`--extra-css`（两种模式通用）

### 命令模板（Agent 默认应执行这一条）

```powershell
.venv\Scripts\python.exe .cursor\skills\html-pdf-studio\scripts\html2pdf.py input.html `
    -o output.pdf --width 1280 [--extra-css fixes.css] [--preview]
```

`--mode continuous` 可写可不写（脚本默认即是）。**不要**在用户未要求时主动
加上 `--mode paged`。

## 两种模式说明（供理解，不可替代上文硬规则）

- **continuous（默认）**：长滚动式网页（提案、落地页、培训页、富 HTML 报告）。
  输出一张超长单页，桌面布局原样保留，不会被分页切断。
- **paged（须用户点名）**：用户明确要 A4/Letter 等标准纸张、正常分页、页码时。
  可设页边距、方向、缩放，配合页眉页脚与书签大纲。

## 工作流

### 1. 先审查源 HTML（决定要不要 `--extra-css`）

读 HTML，重点看四件事——主要影响 `continuous` 模式：

1. **响应式断点**：打印时媒体查询按默认纸宽（~741px）求值，而非 `@page` 尺寸。
   任何 `@media (max-width:N)` 且 N≥741 都会在打印时触发并塌掉桌面布局。逐条写
   覆盖把桌面值用 `!important` 锁回（如
   `.grid{grid-template-columns:repeat(3,1fr)!important}`）。
2. **玻璃拟态**：`backdrop-filter` 模糊在 PDF 里被静默丢弃。脚本已对
   `.glass/[class*=blur]` 自动关闭；若玻璃元素压在忙背景上，再补近不透明底色
   `background:rgba(255,255,255,.88)!important`。
3. **滚动渐显动画**：`fade*/reveal*/animate*/aos` 已自动强制可见；其他以
   `opacity:0` 起始的元素需显式 `opacity:1!important`。
4. **vh/vw 尺寸**：打印里按页面区解析且漂移约 1%，`min-height:100vh` 的首屏会
   异常拉高。用固定 px 覆盖。

把全部覆盖写进一个 CSS 文件，用 `--extra-css` 传入。`paged` 模式断点触发属正常
打印行为，通常无需处理。

### 2. 转换

从仓库根目录执行（PowerShell）。

**默认路径（Agent 未获分页明确要求时执行此条）**：

```powershell
.venv\Scripts\python.exe .cursor\skills\html-pdf-studio\scripts\html2pdf.py input.html `
    -o output.pdf --width 1280 [--extra-css fixes.css] [--preview]
```

**仅当用户明确要求标准分页时**：

```powershell
.venv\Scripts\python.exe .cursor\skills\html-pdf-studio\scripts\html2pdf.py input.html `
    -o output.pdf --mode paged --paper A4 --margin "18 16 20 16" `
    --title "季度报告" --header "季度报告||{date}" --footer "||第 {page} / {pages} 页" `
    --toc --toc-depth 3
```

关键参数：

- `--mode`：脚本默认 `continuous`。**仅用户明确要求分页时**才传 `paged`。
- `--width`：continuous 的页面设计宽度（对齐 8px；非 8px 倍数会触发 MediaBox
  取整 bug 生成幻影页）。
- `--paper / --landscape / --margin`：paged 的纸张、方向、页边距(mm，支持
  `上 右 下 左` 或单值)。
- `--header / --footer`：模板支持 `{title}{page}{pages}{date}` 占位符与
  `左|中|右` 三段对齐。
- `--bookmarks [--toc-depth N]`：仅写 PDF 书签大纲；保留 HTML 文内目录；不插目录页；
  **优先于 `--toc`**。
- `--toc [--toc-depth N] [--toc-title 标题]`：生成 PDF 目录。剥离 HTML 文内目录；
  **paged** 在文前插入带页码的目录页并写书签；**continuous** 仅写书签。
- `--watermark "文字" [--watermark-opacity 0.12]`：斜向平铺文字水印。
- `--title/--author/--subject/--keywords`：PDF 元数据。
- `--password [--owner-password]`：AES-256 加密。
- 多个输入：`input1.html input2.html ...` 会合并成一份 PDF。
- `--replace subs.json`：渲染前替换（脱敏），JSON `[["old","new"], ...]`，更具
  体的串放前面。
- `--forbid words.txt`：逐行禁词；HTML 或最终 PDF 文本命中即中止。务必与
  `--replace` 配对。
- `--crop pixel`：当矢量裁切误判（装饰元素画得比真实内容高）时切换到栅格行扫描。
- `--preview`：额外导出 `<output>.png` 首页缩略图自检。

脚本自动处理：基岩页溢出翻倍重试、内容裁切（同步改写 MediaBox+CropBox）、
CJK 安全输出路径、单页断言、CJK 字体探测内嵌、合并、加密。

### 3. 校验

脚本打印 `OK N 页, ...`。然后：

1. 渲染缩略图肉眼核对（布局完整、无塌陷栅格、背景在、底部无截断）：
   ```python
   import pymupdf
   doc = pymupdf.open("output.pdf")
   doc[0].get_pixmap(dpi=60).save("check.png")
   ```
   或直接加 `--preview` 让脚本生成。
2. 用了脱敏就已对 PDF 文本跑过禁词检查；仍建议在缩略图里目检敏感信息的栅格形态。
3. 留意脚本提示：continuous 模式高度超 14400pt 会破坏旧版 Acrobat（Chrome/
   Firefox/微信预览正常）；要投递 Acrobat 改用 paged 或降低 `--width`。
4. 用了 `--bookmarks`：在阅读器侧栏展开书签确认层级；正文应仍含原 HTML 结构。
   用了 `--toc`：paged 模式检查首页是否为 PDF 目录页；正文不应再有 HTML 文内目录块。
   若某标题缺失，多半是被栅格化导致文本层无法定位。

## 排障与机制

产物异常时（布局塌陷、背景丢失、空白页、幻影第二页、模糊/缺失的中文字形、目录
定位不到、水印/页码字体发糊）阅读
[references/chrome-print-internals.md](references/chrome-print-internals.md)——
它按两种模式记录了本工具所依据的 Chrome 打印渲染规则、裁切与后期加工内幕，以及
CDP 备选路线。
