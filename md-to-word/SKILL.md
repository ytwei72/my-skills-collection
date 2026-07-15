---
name: md-to-word
description: >-
  Converts Markdown (and text-friendly sources) into a well-formatted,
  readable Word (.docx) document with Chinese typography, content-adaptive
  table column widths, header shading, zebra striping, styled headings,
  quote boxes, lists, fenced code blocks, embedded images and page numbers.
  Use when the user asks to convert MD/TXT to Word / .docx / 转 Word /
  转成 word / 导出 Word / Word 版.
disable-model-invocation: false
---

# 文档 → 规范美观的 Word(.docx)

> 本 skill 为项目**默认可自动发现**的 skill 之一；其余 `.cursor/skills/` 下的
> skill 须用户明确点名后才加载(见 `.cursor/rules/skills-lazy-load.mdc`)。

## 何时使用

- 用户要把 **`.md` / `.txt`** 等文本转成 **`.docx` / Word / Word 版 / 导出 Word**。
- 用户强调「格式规范、美观、可读性好」的中文 Word 输出。
- 已有 Markdown、需要交付可编辑的 Word(而非 PDF/HTML)时。

未指定输出路径时:**与源文件同目录、同名改 `.docx`**。

## 首选做法:调用附带脚本

本 skill 附带成品转换器,覆盖绝大多数文档,优先直接调用(不要逐段手工搭建
Word):

```bash
python .cursor/skills/md-to-word/scripts/md_to_docx.py <input.md> [output.docx]
```

- 依赖 `python-docx`(`pip install python-docx`);仓库有 `.venv` 时用
  `.venv\Scripts\python.exe` 调用。
- 省略 `output.docx` 时与源文件同目录、同名改 `.docx`。
- 脚本为**幂等**:重复运行覆盖同名输出。

脚本无法满足时(需公文红头、特殊模板、复杂分栏/图文混排等),再按下文
「格式化规范」由 Agent 用 `python-docx` 定制;公文格式化优先考虑
`official-doc-formatter`(须用户点名)。

## 核心能力:表格列宽内容自适应

**要求:表格各列宽度按各列内容自适应**,而非平均分。脚本实现:

1. 对每列取所有行(含表头)的**最大显示宽度**;中文/全角字符按 2、其余按 1
   计(CJK 感知),单元格内 `<br>` 分行取各行最大值。
2. 单列宽度设上限(`cap_units`,默认 52)避免超长描述列独吞整表宽度。
3. 各列按自然宽度**成比例**分配到页面可用宽度,并设最小列宽(默认 1.4cm)。
4. 关闭 `autofit`、写入固定 `tblGrid` + `tblLayout=fixed`,保证 Word 中稳定
   呈现所算列宽。

效果:序号/状态等短列自动收窄,说明/描述等长列自动加宽,整体不溢出页面。

## 格式化规范(提升可读性与美观)

统一配置集中在脚本顶部常量,便于整体调色/调字号。

### 字体(中文排版)

| 元素 | 中文字体 | 说明 |
|------|----------|------|
| 一级/章节/子标题 | 黑体 | 分级字号 22/15/12.5/11pt,主色渐进 |
| 正文、表格 | 宋体 | 正文 10.5pt、表格 10pt |
| 引用块 | 楷体 | 弱化色,区分说明性文字 |
| 内联/围栏代码、路径 | Consolas | 代码略小、标红,路径清晰可辨 |

### 版式与配色

- **标题分级**:`#` 居中深蓝 + 下装饰线;`##` 深蓝章节;`###` 亮蓝 + 左侧竖条;
  `####` 次级亮蓝。标题设 `keep_with_next`,避免孤行落在页尾。
- **引用块** `>`:浅蓝底纹 + 左边框提示框,楷体弱化色,连续多行自动合并。
- **列表**:有序/无序悬挂缩进,项目符号用主题色,1.5 倍行距。
- **围栏代码块** ```` ``` ````:浅灰底纹 + 左边框,等宽字体整块呈现。
- **图片** `![](path)`:居中嵌入(相对源文件解析路径),缺失时占位提示不报错。
- **内联**:`**加粗**`、`*斜体*`、`` `代码` ``、`[文本](url)`(链接蓝色下划线)。

### 表格美化

- 表头深蓝底纹 + 白字加粗,并设**跨页重复表头**。
- 普通表隔行浅蓝**斑马纹**,内容居中;识别「字段/说明」两列表时左列高亮加粗、
  右列左对齐,适合逐条说明式内容。
- 全表统一细边框(浅蓝)、单元格内边距、垂直居中、1.5 倍行距。
- 支持单元格内 `<br>` 换行。

### 页面与整体

- A4,页边距上 2.5 / 下 2.3 / 左右 2.8cm;页脚居中页码。
- 全篇统一间距刻度(段前/段后)、统一 1.5 倍行距,保证呼吸感与一致性。

## 工作流程

1. 确认源文件与输出路径(未给则同目录同名 `.docx`)。
2. 优先运行脚本转换;检查表格数量、列宽是否合理(短列窄、长列宽、不溢页)。
3. 如需定制超出脚本能力,按「格式化规范」用 `python-docx` 手工增强。
4. 交付:说明输出路径,可直接用 Word 打开编辑;必要时提示可再转 PDF。

## 延伸阅读

配色/字号/列宽算法等可调参数与扩展说明见 [reference.md](reference.md)
(按需打开,避免占满上下文)。
