# md-to-rich-html — 参考扩充

## 中间格式与命令（可选，环境具备时使用）

将难解析源转为 MD/HTML 再套版式，避免在对话里「猜」二进制内容：

- Pandoc 示例：`pandoc -f docx -t markdown -o intermediate.md input.docx`
- 转为裸 HTML 再包壳：`pandoc -s -f docx -t html5 -o raw.html input.docx`（再用本技能统一 `<style>` 与布局）

无 Pandoc 时：不要伪造 docx 正文；引导用户导出或粘贴。

## 版式模块库（组合使用）

- **Hero**：大标题 + 一行副标题 + 可选日期/标签 pill。
- **Section 卡片**：`h2` 左侧色条或上边框区分章节。
- **Callout**：左侧实线 + 浅底，用于摘要、安全原则。
- **两栏 / 三栏 Grid**：`grid-template-columns: repeat(3,1fr)` + `@media (max-width: 680px) { 1fr }`。
- **Figure 区**：虚线边框 + 浅底；`.figure-caption` 与 SVG 之间保留 `margin-top`（可用 `clamp()`）。

## SVG 技术注意

- `viewBox` 必须包含所有子元素外接矩形；箭头、底部框的 `y+height` 算进高度。
- `preserveAspectRatio="xMidYMid meet"` 常用于宽图在窄屏缩放。
- `overflow: visible` 在父级裁切时可能仍无效，以 **增大 viewBox** 为主手段防裁切。
- 深色模式：关键描边/文字在 `@media (prefers-color-scheme: dark)` 下单独设类或 `defs` 内 style。

## 不宜自动化的内容

- 需要真实数据的统计图（精确柱状/折线）：除非 MD 内给出表格数据，否则用 **示意** 或文字 + 简单比例条，并注明「示意」。
- 地图、复杂 UML：改为简化框图或拆成多图。

## 与用户协作

若用户要求「打印 PDF」：在 HTML 末尾可加 `@media print` 隐藏装饰、分页控制；或提示用户浏览器打印为 PDF。
