# html-pdf-studio

把 HTML（本地文件或 `http(s)` URL）**全功能**转换成 PDF：连续单页与标准分页双
模式，外加页眉页脚页码、书签目录、水印、元数据、加密、合并与预览自检。

渲染交给本机无头 Chrome/Edge，版面加工交给 PyMuPDF——除 PyMuPDF 外零运行时依赖。

## 它能做什么

| 能力 | 说明 |
|---|---|
| **continuous 连续单页** | 渲染到超高基岩页，量出真实内容底边再裁切；桌面布局原样保留、不分页、文本可选 |
| **paged 标准分页** | A4/A3/A5/Letter/Legal、横纵向、mm 页边距、打印缩放 |
| **页眉/页脚/页码** | 模板支持 `{title}{page}{pages}{date}` 与 `左\|中\|右` 三段对齐 |
| **书签目录(TOC)** | 由 HTML 标题 `h1..hN` 自动生成嵌套大纲 |
| **文字水印** | 斜向平铺，可调不透明度与字号 |
| **PDF 元数据** | 标题/作者/主题/关键词 |
| **加密** | AES-256，用户/所有者密码 |
| **多文件合并** | 多个输入按序合并为一份 PDF |
| **URL 输入** | 直接抓取在线 HTML（自动注入 `<base>` 解析相对资源） |
| **脱敏 + 禁词校验** | 渲染前替换敏感串，并对 HTML 与最终 PDF 文本核查泄漏 |
| **预览自检** | 导出首页缩略图 PNG |

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

## 用法

**默认（连续单页，保留桌面布局）**——大多数场景应使用此命令：

```bash
python scripts/html2pdf.py input.html -o output.pdf --width 1280
```

`--mode continuous` 可省略（脚本默认即是）。

**仅当用户明确要求标准分页时**（A4、页码、多页打印）：

```bash
python scripts/html2pdf.py report.html -o report.pdf \
    --mode paged --paper A4 --margin "18 16 20 16" \
    --title "季度报告" --author "DocsRep" \
    --header "季度报告||{date}" --footer "||第 {page} / {pages} 页" \
    --toc --toc-depth 3 --watermark "机密" --preview
```

多文件合并 + 加密：

```bash
python scripts/html2pdf.py cover.html body.html appendix.html \
    -o bundle.pdf --mode paged --password "open123"
```

### 主要参数

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
| `--toc / --toc-depth` | — / 3 | 书签大纲及深度 |
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
`--extra-css` 锁回桌面值。书签目录依赖 PDF 文本层，被栅格化（受 CSS `filter`
影响）的标题定位不到。

完整原理——两个视口的媒体查询行为、隐藏的 1.5 倍缩印、PDF 尺寸上限、CJK 字体陷
阱、裁切与后期加工内幕、CDP 备选路线——见
[references/chrome-print-internals.md](references/chrome-print-internals.md)。

## 作为 Agent 技能

本目录即一个 Cursor/Claude 技能：放在 `.cursor/skills/html-pdf-studio/`，
助手会审查源 HTML、自动生成断点锁定、运行转换并肉眼核验产物。详见
[SKILL.md](SKILL.md)。

### Agent 模式选择（必读）

| 用户意图 | 应选模式 |
|---|---|
| 「HTML 转 PDF」「导出 PDF」等，**未说分页** | **continuous**（默认，可省略 `--mode`） |
| 「单页 / 不分页 / 长图式 / 保留网页布局」 | **continuous** |
| HTML 有章节、表格、文内目录，但用户未要求分页 | **continuous**（禁止擅自改 paged） |
| 「A4 / 标准分页 / 多页 / 页码 / 页眉页脚含页码」 | **paged**（须用户明确点名） |
| 只说「报告」但未说分页 | **先问**；不回复则 **continuous** |

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
| 无目录书签 | 由 HTML `h1..hN` **自动生成嵌套书签大纲(TOC)** |
| 无元数据/水印/加密 | PDF 元数据、斜向文字水印、**AES-256 加密** |
| 仅本地单文件 | 支持 **URL 输入**与**多文件合并**为一份 PDF |
| 玻璃拟态全靠手写 CSS | 内置对 `.glass/[class*=blur]` 的自动降级 |
| 无产物自检 | `--preview` 导出首页缩略图 PNG |
| 辅助文件读取易因 BOM 失败 | 辅助文件改用 `utf-8-sig`，容忍 PowerShell 的 BOM |

沿用并重写的内核：矢量 bbox / 像素行扫描两路内容检测、MediaBox+CropBox 同步改写、
基岩页溢出翻倍重试、脱敏替换 + 禁词泄漏校验。
