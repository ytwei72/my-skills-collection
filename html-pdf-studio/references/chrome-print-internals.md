# Chrome 打印渲染机制与本工具实现内幕

本文解释 `html-pdf-studio` 为什么这样设计，以及产物异常时该怎么排查。结论核
对自 Chromium 源码 / W3C 规范 / 生产实践（Gotenberg），并按本工具的两种模式
（`continuous` 连续单页 / `paged` 标准分页）分别说明。

## 目录

- [两种模式，两种几何](#两种模式两种几何)
- [为什么连续页的高度只能量不能算](#为什么连续页的高度只能量不能算)
- [媒体查询 vs @page —— 两个视口](#媒体查询-vs-page--两个视口)
- [隐藏的 1.5 倍缩印](#隐藏的-15-倍缩印)
- [单位取整与幻影页](#单位取整与幻影页)
- [PDF 尺寸上限](#pdf-尺寸上限)
- [PDF 输出中的保真损失](#pdf-输出中的保真损失)
- [资源就绪与字体](#资源就绪与字体)
- [中文/CJK 注意事项](#中文cjk-注意事项)
- [裁切内幕（continuous）](#裁切内幕continuous)
- [后期加工内幕（PyMuPDF）](#后期加工内幕pymupdf)
- [备选路线：CDP 实测高度](#备选路线cdp-实测高度)

## 两种模式，两种几何

| 维度 | continuous（连续单页） | paged（标准分页） |
|---|---|---|
| `@page` | `size: 宽px 基岩px; margin:0` | `size: A4/Letter…; margin: mm` |
| 适用 | 长滚动网页、落地页、提案 | 文档类 HTML、报告、合同 |
| 高度 | 渲染后量内容底边再裁 | 由纸张固定，正常分页 |
| 断点 | 仍按 ~741px 触发（需锁定） | 按页面区宽触发（属正常打印） |
| 页码 | 无意义（仅 1 页） | 有意义，可加页眉页脚 |

两种模式共用同一段注入 CSS（颜色保真、关动画、强制显示 scroll-reveal、玻璃
拟态降级），仅 `@page` 不同。

## 为什么连续页的高度只能量不能算

屏幕上量得的 `scrollHeight` 不等于打印版面的高度：

- `--print-to-pdf` 用 **print** 媒体 CSS 排版；在屏幕上测量的是另一套布局。
- 打印时媒体查询按另一个宽度求值（见下节），断点位置会变。
- 测量之后才到达的 Web 字体会改变行高。
- px→inch→pt 的换算链取整不单调（puppeteer#2278）。

所以本工具不预测高度：渲染到一张超高"基岩页"，从 PDF 自身量出真实内容底边，
再把页面框裁到刚好。**高度是裁出来的，不是算出来的**，因而精确。

## 媒体查询 vs @page —— 两个视口

依 css-page-3 §7.1，媒体查询**必须忽略 `@page size`**（防循环规则），按默认
纸张求值。Chrome 实测：媒体查询宽度 ≈ **741px**（US Letter 减默认页边距），
与任何 `@page` 声明无关。

与此同时 vw/vh 按**首页页面区**解析——它**会**采纳 `@page size`——并带约 1%
的设备单位取整漂移。于是同一文档里，媒体查询按 741px、vw 按 @page 宽度，两套
视口同时存在。容器查询（container query）跟随实际布局容器，是打印里唯一可靠
的响应式机制。

实操规则：

- `continuous` 模式：把每个 ≥741px 的断点用 `--extra-css` 锁回桌面值（加
  `!important`，如 `.grid{grid-template-columns:repeat(3,1fr)!important}`），
  并把 `min-height:100vh` 之类换成固定 px。
- `paged` 模式：页面区宽通常较窄（A4 纵向约 794px 减边距），断点会大量触发，
  这属于正常文档打印行为，一般无需锁定。

## 隐藏的 1.5 倍缩印

Blink 里 `printingMaximumShrinkFactor = 1.5`：当最宽的不可断内容超过页面宽
度，Chrome 会重排并把**整篇按最多 1.5 倍缩小**以塞下（再超就裁切）。一个溢出
元素会改变全文档的比例。务必让实际内容宽度 ≤ `--width`（continuous）或页面区
宽（paged）。

## 单位取整与幻影页

Chrome 把 px→inch→pt 换算时取整误差可达约 0.2%（MediaBox 73pt 变成
72.96）。高度差零点几 pt 就会把一行挤到第二页。本工具的缓解：

- 宽高对齐到 8px（8px = 6pt 整）；
- `continuous` 的基岩页刻意巨大，渲染时取整不影响；
- CDP 路线的等效技巧是 `pageRanges:"1"`（丢弃取整溢出）。

## PDF 尺寸上限

- 14400pt（200in，≈19200px）是 ISO 32000-1 附录 C 给出的 **Acrobat 实现上
  限**，不是格式上限；PDF 2.0 已取消。
- Chrome 乐于写更大的页（实测 22500pt，无钳制、无 UserUnit）。
  Chrome/Firefox/PDFium/微信能正常渲染；旧版 Acrobat 可能拒绝。
- `continuous` 模式产物超 14400pt 时脚本会给出提示，那是兼容性提醒而非错误。
  如需投递 Acrobat，改用 `paged` 模式或降低 `--width`。

## PDF 输出中的保真损失

| 特性 | 在 PDF 里的表现 | 处理 |
|---|---|---|
| `backdrop-filter` 模糊 | **静默丢弃**（crbug 40895818），半透明底色还在 | 注入 CSS 已对 `.glass/[class*=blur]` 关闭；忙背景上再加近不透明底色 |
| `background-attachment: fixed` | 只画在第一页，偏离规范 | 注入 CSS 强制 `scroll` |
| `box-shadow` | 正常，保持矢量 | — |
| 透视/3D 变换 | 按单位矩阵渲染（SkPDF） | 打印里避免使用 |
| 受 CSS `filter` 影响的元素 | 被栅格化，文字失去可选性 | 不要给含文字的容器加 filter |
| 背景色/渐变 | 需 `print-color-adjust: exact` | 注入 CSS 已全局加上 |

## 资源就绪与字体

CLI `--print-to-pdf` 只等 `load` 事件——不等字体、不等 JS 注入的内容。本工具
传入：

- `--virtual-time-budget=10000`：快进定时器驱动的 JS（实验性；不等慢网络/慢
  CPU），可用 `--virtual-time` 调大；
- `--run-all-compositor-stages-before-draw`：确保捕获前栅格化完成。

仍缺字体或晚加载图片时：调大 `--virtual-time`、把资源内联为 data URL、或在
`<head>` 预加载字体。注意无头模式会静默拒绝 `@page` 边距盒 CSS 引用的外部资
源——那些必须内联为 data URL。`loading="lazy"` 图片在当前无头打印里正常（实测
Chrome 149）；老版本可用 `--replace` 改成 `loading="eager"`。

## 中文/CJK 注意事项

- HTML 里设 `<html lang="zh-CN">`，否则 Linux 上 fontconfig 可能给正文选到
  Noto CJK 的 Thin 字重。
- Docker/CI 镜像需装 `fonts-noto-cjk`，否则 CJK 全成豆腐块。
- CJK 字体常只带 Regular；`font-weight:600+` 会触发合成粗体，PDF 里发糊。尽量
  载入真实字重文件（如 Noto Sans SC 500/700）。
- 页眉/页脚/水印里的中文由 **PyMuPDF** 而非浏览器绘制：脚本会探测本机 CJK 字
  体（Windows 微软雅黑/黑体/宋体，macOS 苹方，Linux Noto）并子集内嵌；找不到
  时退回 Helvetica（汉字会丢失），此时请确认系统装有上述字体。

## 裁切内幕（continuous）

- 内容底边取自 `page.get_bboxlog()`——渲染级命令日志，覆盖文本、图像、矢量路
  径并展开 Form XObject 内部（`get_text('blocks')`+`get_drawings()` 会漏掉
  XObject 内部与内联图像）。跳过 `ignore-text`（不可见文本），也跳过高度 ≥97%
  页高的填充（铺满基岩页的页面背景，否则并集会退化成整页）。
- 像素模式（`--crop pixel`）按 24dpi 栅格化、自底向上扫描水平方差超阈值的行；
  垂直渐变背景在水平方向均匀，不会被当成内容。当矢量模式保留了延伸到真实内容
  以下的装饰几何时改用它。
- MediaBox 与 CropBox 用 `xref_set_key` 在原始 PDF（y-up）坐标里改写成同一
  矩形。这样既绕开 PyMuPDF `set_mediabox` 删除 CropBox 的副作用，也消除"有的
  查看器看 MediaBox、有的看 CropBox∩MediaBox"的歧义。
- 裁切后紧跟 `normalize_page_origin`：用 `show_pdf_page` 把可见区重绘到
  `[0,0,w,h]`。否则 MediaBox.y0 非零，书签 dest 为大数值绝对坐标，WPS 等阅读器
  会全部跳到页首。

## 后期加工内幕（PyMuPDF）

所有版面增量都在渲染后由 PyMuPDF 完成，独立于浏览器，便于精确控制字体与不透
明度，两种模式通用：

- **页眉/页脚**：用 `TextWriter` 逐页写。模板支持 `{title}{page}{pages}{date}`
  占位符与 `左|中|右` 三段对齐语法。页码基于合并后整本计数。
- **PDF 书签（`--bookmarks`）**：从 HTML 抽取 `h1..hN`（抽取时忽略 `nav.toc` 内
  标题以免重复），在 PDF 文本层定位后 `set_toc`。**不改正文、不插页**；与
  continuous/paged 无关。同时指定 `--toc` 时**书签优先**。
- **PDF 目录（`--toc`）**：渲染前剥离 HTML 文内目录块；**paged** 在文前插入目录页
  （层级缩进 + 点引导符 + 页码），再按偏移写入书签；**continuous** 仅剥离 + 书签。
  标题超 40 字截断以提高 `search_for` 命中率；定位在插入目录页**之前**完成。
  同一标题多处出现时（文内交叉引用），取 **y 单调递增** 的命中，避免抢先定位
  到前文引用。 *书签/目录均依赖文本层——若标题被栅格化（见保真损失）则定位不到。*
- **水印**：`TextWriter` + 绕页心旋转 45° 的 `Matrix`，`opacity` 控制透明度。
  注意 `page.insert_text` 的 `rotate` 只接受 0/90/180/270，斜向必须走
  `TextWriter` 的 `morph`。
- **元数据**：`set_metadata`（标题/作者/主题/关键词）。
- **加密**：`save(encryption=PDF_ENCRYPT_AES_256, user_pw=, owner_pw=,
  permissions=…)`。加密后脚本跳过禁词文本复核（无法稳定提取）。
- **合并**：每个输入各自渲染成 PDF，再 `insert_pdf` 拼接成一本。

## 备选路线：CDP 实测高度

Gotenberg 8 生产实现 `singlePage=true`（tasks.go）：

```
Emulation.setEmulatedMedia(media="print")
m = Page.getLayoutMetrics()              # cssContentSize.height 即权威高度
Page.printToPDF(paperWidth = W/96,
                paperHeight = m.cssContentSize.height/96,
                marginTop=0, ..., pageRanges="1")   # "1" 丢弃取整溢出
```

优点：无需基岩页、无需裁切，渲染时 MediaBox 即精确。缺点：需要 CDP 客户端
（websocket）而非裸 CLI；lazy-load / 视口相关布局仍可能测偏（gotenberg#1046）。
本工具刻意停留在 CLI+裁切路线以保持"除 PyMuPDF 外零运行时依赖"；仅当某类页面
持续击穿裁切启发式时，才考虑切到 CDP。
