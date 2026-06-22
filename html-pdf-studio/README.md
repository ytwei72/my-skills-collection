# html-pdf-studio

把 HTML（本地文件或 `http(s)` URL）**全功能**转换成 PDF：连续单页与标准分页双
模式，外加页眉页脚页码、书签、PDF 目录页、水印、元数据、加密、合并与预览自检。

渲染交给本机无头 Chrome/Edge，版面加工交给 PyMuPDF——除 PyMuPDF 外零运行时依赖。

## 它能做什么

| 能力 | 说明 |
|---|---|
| **continuous 连续单页** | 渲染到超高基岩页，量出真实内容底边再裁切；桌面布局原样保留、不分页、文本可选 |
| **paged 标准分页** | A4/A3/A5/Letter/Legal、横纵向、mm 页边距、打印缩放 |
| **页眉/页脚/页码** | 模板支持 `{title}{page}{pages}{date}` 与 `左\|中\|右` 三段对齐 |
| **PDF 书签**（`--bookmarks`） | 按 HTML 标题写阅读器侧栏大纲；**不改正文**、不插目录页 |
| **PDF 目录**（`--toc`） | 剥离 HTML 文内目录；paged 模式在文前插入带页码的目录页，并写书签 |
| **文字水印** | 斜向平铺，可调不透明度与字号 |
| **PDF 元数据** | 标题/作者/主题/关键词 |
| **加密** | AES-256，用户/所有者密码 |
| **多文件合并** | 多个输入按序合并为一份 PDF |
| **URL 输入** | 直接抓取在线 HTML（自动注入 `<base>` 解析相对资源） |
| **脱敏 + 禁词校验** | 渲染前替换敏感串，并对 HTML 与最终 PDF 文本核查泄漏 |
| **预览自检** | 导出首页缩略图 PNG |

## `--bookmarks` 与 `--toc` 的区别

两者都根据 HTML 的 `h1..hN` 标题生成导航结构，但**用途与对正文的影响不同**。
**同时指定时 `--bookmarks` 优先**（只写书签，忽略 `--toc` 的目录页与 HTML 剥离）。

| | `--bookmarks` 书签 | `--toc` 目录 |
|---|---|---|
| **用户怎么说** | 「加书签」「生成大纲」「侧栏导航」 | 「PDF 目录」「添加目录」「更新目录」「目录页」 |
| **阅读器表现** | 侧栏可展开跳转，**正文无新增页面** | 文前插入独立目录页（点线 + 页码），侧栏也有书签 |
| **HTML 文内目录** | **保留**（`nav.toc` 等原样输出） | **移除**（避免与 PDF 目录页重复） |
| **continuous** | ✅ 适用 | ⚠️ 仅写书签（单页无法做分页目录页） |
| **paged** | ✅ 适用 | ✅ 插入目录页 + 书签 |
| **是否改变页数** | 否 | paged 模式下 +N 页目录 |
| **层级深度** | `--toc-depth N`（默认 3） | 同左 |
| **目录页标题** | — | `--toc-title`（默认「目录」） |

**选用建议**

- 只要阅读器里能点章节跳转、又不想动版面 → `--bookmarks`
- 要纸质/打印风格的目录页、且正文里不要 HTML 目录块 → `--toc`（paged）
- 两者都写了 → 按书签处理，脚本会提示

## 为什么这样设计

Chrome 的打印管线无法提前告诉你页面的打印高度：打印媒体查询按默认纸宽
（~741px）而非 `@page` 尺寸求值、视口单位会漂移、Web 字体改变行高、px→inch→pt
换算取整还会生出幻影页（[puppeteer#2278](https://github.com/puppeteer/puppeteer/issues/2278)）。

所以 `continuous` 模式不预测高度：渲染到超高"基岩页"，再从 PDF 自身量出真实内容
底边并把 MediaBox+CropBox 裁到刚好。**高度是裁出来的，不是算出来的**，因而精确。
`paged` 模式则交给纸张正常分页——**仅当用户明确要求标准分页 / A4 / 页码时使用**；
不要因为 HTML 里有章节、表格或目录就擅自选用 paged。

## 环境要求

- Python 3.10+ 且安装 [`pymupdf`](https://pypi.org/project/PyMuPDF/)
- 本机 Chrome 或 Edge（自动探测，或用 `--chrome` 指定）
- 页眉/页脚/水印含中文时，需系统装有 CJK 字体（Windows 微软雅黑/黑体/宋体、
  macOS 苹方、Linux Noto CJK；脚本自动探测）

## 示例指令

以下命令均从**仓库根目录**执行。Windows 用 `.venv\Scripts\python.exe`，Linux/macOS
把路径换成 `.venv/bin/python` 即可。

### 1. 默认：HTML 转 PDF（连续单页）

用户只说「导出 PDF」「网页转 PDF」，未要求分页：

```powershell
.venv\Scripts\python.exe .cursor\skills\html-pdf-studio\scripts\html2pdf.py `
    ReportsDoc\培训\2.1实例\2.1实例_数据处理_具体操作指南.html `
    -o ReportsDoc\培训\2.1实例\2.1实例_数据处理_具体操作指南.pdf `
    --width 1280 --preview
```

### 2. 加书签（不改版面、不插目录页）

continuous 或 paged 均可；保留 HTML 里的 `nav.toc`：

```powershell
# 连续单页 + 书签
.venv\Scripts\python.exe .cursor\skills\html-pdf-studio\scripts\html2pdf.py `
    input.html -o output.pdf --width 1280 --bookmarks --toc-depth 3

# A4 分页 + 书签（无目录页）
.venv\Scripts\python.exe .cursor\skills\html-pdf-studio\scripts\html2pdf.py `
    input.html -o output.pdf --mode paged --paper A4 `
    --bookmarks --toc-depth 3
```

### 3. 加 PDF 目录页（paged，剥离 HTML 文内目录）

用户明确要「PDF 目录」「目录页」：

```powershell
.venv\Scripts\python.exe .cursor\skills\html-pdf-studio\scripts\html2pdf.py `
    input.html -o output.pdf --mode paged --paper A4 --margin "18 16 20 16" `
    --toc --toc-depth 3 --toc-title "目录"
```

### 4. 标准分页报告（页眉页脚 + 目录）

```powershell
.venv\Scripts\python.exe .cursor\skills\html-pdf-studio\scripts\html2pdf.py `
    report.html -o report.pdf `
    --mode paged --paper A4 --margin "18 16 20 16" `
    --title "季度报告" --author "DocsRep" `
    --header "季度报告||{date}" --footer "||第 {page} / {pages} 页" `
    --toc --toc-depth 3 --watermark "内部资料" --preview
```

### 5. 响应式网页 + 断点锁定 CSS

```powershell
.venv\Scripts\python.exe .cursor\skills\html-pdf-studio\scripts\html2pdf.py `
    landing.html -o landing.pdf --width 1280 `
    --extra-css fixes-print.css --preview
```

### 6. 多文件合并

```powershell
.venv\Scripts\python.exe .cursor\skills\html-pdf-studio\scripts\html2pdf.py `
    cover.html body.html appendix.html -o bundle.pdf `
    --mode paged --paper A4 --bookmarks
```

### 7. 在线 URL

```powershell
.venv\Scripts\python.exe .cursor\skills\html-pdf-studio\scripts\html2pdf.py `
    "https://example.com/page.html" -o page.pdf --width 1280
```

### 8. 脱敏导出 + 禁词校验

```powershell
.venv\Scripts\python.exe .cursor\skills\html-pdf-studio\scripts\html2pdf.py `
    sensitive.html -o safe.pdf --replace subs.json --forbid words.txt --preview
```

### 9. 加密 PDF

```powershell
.venv\Scripts\python.exe .cursor\skills\html-pdf-studio\scripts\html2pdf.py `
    input.html -o locked.pdf --password "open123" --owner-password "admin456"
```

### 10. 裁切误判时改用像素扫描

```powershell
.venv\Scripts\python.exe .cursor\skills\html-pdf-studio\scripts\html2pdf.py `
    input.html -o output.pdf --width 1280 --crop pixel --preview
```

## 主要参数

| 参数 | 默认 | 用途 |
|---|---|---|
| `--mode` | continuous | `continuous` 单页 / `paged` 分页 |
| `--width` | 1280 | continuous 页面宽度(CSS px，对齐 8px) |
| `--bedrock` | 18000 | continuous 基岩页初始高度，溢出自动翻倍 |
| `--padding` | 32 | continuous 内容下方留白 px |
| `--crop` | vector | `vector`(bbox 日志) / `pixel`(栅格行扫描) |
| `--paper` | A4 | paged 纸张 A3/A4/A5/Letter/Legal |
| `--landscape` | — | paged 横向 |
| `--margin` | "16 16 18 16" | paged 页边距 mm |
| `--scale` | 1.0 | 打印缩放 0.1~2 |
| `--extra-css` | — | 追加到注入打印样式后的 CSS(断点锁定/玻璃降级) |
| `--header / --footer` | — | 页眉页脚模板 |
| `--bookmarks` | — | 仅写 PDF 书签大纲；优先于 `--toc` |
| `--toc` | — | 剥离 HTML 文内目录；paged 插入目录页 + 书签 |
| `--toc-depth` | 3 | 书签/目录采用的标题层级 h1..hN |
| `--toc-title` | 目录 | PDF 目录页标题（仅 `--toc`） |
| `--watermark / --watermark-opacity / --watermark-size` | — / 0.12 / 60 | 文字水印 |
| `--title/--author/--subject/--keywords` | — | PDF 元数据 |
| `--password / --owner-password` | — | AES-256 加密 |
| `--replace` | — | JSON `[["old","new"],...]` 渲染前替换(脱敏) |
| `--forbid` | — | 逐行禁词；HTML 或最终 PDF 文本命中即中止 |
| `--virtual-time` | 10000 | Chrome `--virtual-time-budget` 毫秒 |
| `--preview` | — | 额外导出 `<output>.png` 首页缩略图 |

### 自动处理的事项

- 滚动渐显动画强制可见（`fade*/reveal*/animate*/aos`）
- 背景色与渐变保留（`print-color-adjust: exact`）
- `background-attachment: fixed` 归一为 `scroll`
- 玻璃拟态降级（关闭 `backdrop-filter`）
- continuous 溢出自动翻倍重试直到单页装下
- MediaBox 与 CropBox 同步改写（查看器兼容）
- 单页断言 + 针对 PDF 文本层的禁词泄漏复核
- 页眉页脚水印含中文时自动探测并内嵌系统 CJK 字体
- continuous 输出超 14400pt 时给出 Acrobat 兼容性提示

### 仍需手工的事项

`continuous` 模式下 ≥741px 的响应式断点会在打印时触发并塌掉桌面栅格——用
`--extra-css` 锁回桌面值。书签/目录定位依赖 PDF 文本层，被栅格化（受 CSS `filter`
影响）的标题可能定位不到。`--toc` 会移除 HTML 中的 `nav.toc` 等文内目录块；
`--bookmarks` 则保留它们。

完整原理——两个视口的媒体查询行为、隐藏的 1.5 倍缩印、PDF 尺寸上限、CJK 字体陷
阱、裁切与后期加工内幕、CDP 备选路线——见
[references/chrome-print-internals.md](references/chrome-print-internals.md)。

## 作为 Agent 技能

本目录即一个 Cursor/Claude 技能：放在 `.cursor/skills/html-pdf-studio/`，
助手会审查源 HTML、自动生成断点锁定、运行转换并肉眼核验产物。详见
[SKILL.md](SKILL.md)。

### Agent 模式选择（必读）

| 用户意图 | 应选模式 | 导航参数 |
|---|---|---|
| 「HTML 转 PDF」「导出 PDF」等，**未说分页** | **continuous** | 无 |
| 「单页 / 不分页 / 长图式 / 保留网页布局」 | **continuous** | 无 |
| 「加书签 / 大纲 / 侧栏导航」 | 保持用户指定的 continuous/paged | **`--bookmarks`** |
| 「PDF 目录 / 添加目录 / 目录页」 | 通常 **paged**（先确认） | **`--toc`** |
| 「A4 / 标准分页 / 多页 / 页码」 | **paged** | 按需 `--bookmarks` 或 `--toc` |
| HTML 有章节、表格、文内目录，但未要求分页 | **continuous** | 按需 `--bookmarks` |

常见误用：看到 h1/h2、`<table>`、目录就推断「报告类文档 → paged」。**结构不等于
分页需求**；paged 是用户显式要求的产物形态，不是 Agent 对 HTML 类型的猜测。
完整硬规则见 [SKILL.md](SKILL.md) 的「Agent 必读：模式选择」一节。

## 许可证

MIT

## 附录：相比 onepage-pdf 的改进

本技能是 `onepage-pdf` 的超集——沿用并重写其"连续单页裁切"内核，同时补齐它欠缺
的能力：

| onepage-pdf 的欠缺 | html-pdf-studio 的改进 |
|---|---|
| 只能单页长图 | 新增 **`paged` 标准分页**（A4/A3/A5/Letter/Legal、横纵向、mm 页边距、打印缩放） |
| 无页眉/页脚/页码 | 模板化页眉页脚，支持 `{title}{page}{pages}{date}` 与 `左\|中\|右` 三段对齐 |
| 无书签/目录 | **`--bookmarks`** 侧栏大纲；**`--toc`** 剥离 HTML 目录并插入 PDF 目录页 |
| 无元数据/水印/加密 | PDF 元数据、斜向文字水印、**AES-256 加密** |
| 仅本地单文件 | 支持 **URL 输入**与**多文件合并**为一份 PDF |
| 玻璃拟态全靠手写 CSS | 内置对 `.glass/[class*=blur]` 的自动降级 |
| 无产物自检 | `--preview` 导出首页缩略图 PNG |
| 辅助文件读取易因 BOM 失败 | 辅助文件改用 `utf-8-sig`，容忍 PowerShell 的 BOM |

沿用并重写的内核：矢量 bbox / 像素行扫描两路内容检测、MediaBox+CropBox 同步改写、
基岩页溢出翻倍重试、脱敏替换 + 禁词泄漏校验。
