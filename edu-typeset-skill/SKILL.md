---
name: edu-typeset
disable-model-invocation: true
description: >
  按出版印刷标准对文档进行专业排版与格式化，生成高质量 .docx 文件。适用于：用户提交任何文档（教辅材料、讲义、报告、教案等）并要求"出版排版"、"专业格式"、"印刷标准"、"重新排版"、"格式规范化"时。
  支持多种文档类型，内置"英语教学辅导材料"标准模板（见 assets/template-en-edu.js）。
  凡涉及文档排版、格式整理、出版标准化的任务，均应使用本 skill，即使用户未明确说"排版"。
  排版完成后，自动对文档内容进行理解提炼，在文末生成"附录：知识点总结"，将核心规律、重要规则、易混淆概念以结构化表格或框形式呈现。
---

# 出版印刷级文档排版 Skill

## 概览

本 skill 将任意文档转换为符合出版印刷标准的专业 .docx 文件，并在文末自动附加"附录：知识点/规则总结"。

**支持输入格式**：.docx、.txt、.md、.pdf（文本型）  
**输出格式**：.docx（标准 OOXML）  
**依赖工具**：Node.js + docx.js（安装说明见下方"环境依赖"）

---

## 环境依赖

### docx.js 安装

```bash
# 全局安装（推荐，一次安装后所有任务可用）
npm install -g docx

# 验证安装
node -e "require('docx'); console.log('docx ok')"
```

> **版本要求**：docx ≥ 8.x（本 skill 使用 9.x API）。  
> 如全局安装受限，可在工作目录执行 `npm install docx`，脚本中 require 路径改为 `./node_modules/docx`。

### 其他依赖

```bash
# 文本提取（读取原始文档内容）
# pandoc 通常已预装；如缺失：
apt-get install pandoc   # Linux
brew install pandoc      # macOS

# Python 脚本（解包/验证 docx，来自 docx skill）
# 已包含在 /mnt/skills/public/docx/scripts/ 下，无需额外安装
```

---

## 执行流程

### Step 1：读取原始文档

```bash
# 教辅含填空时优先：直接从 docx 抽文本（避免 pandoc 把 _ 转成 \_）
# 若使用 pandoc：
pandoc <input_file> -t markdown -o /tmp/content.md
```

**填空下划线**：`pandoc docx→markdown` 会把 `______` 写成 `\_\_\_\_`（Markdown 转义）。写入 docx 前**必须**对每段文本调用 `normalizeExtractedText()`（见 `assets/template-en-edu.js`）；`engPara` / `cnPara` 已内置。禁止用 `.replace(/_{2,}/g, '')` 删掉下划线。

分析文档，识别：
- **文档类型**（教辅材料 / 报告 / 教案 / 其他）
- **层级结构**（标题层级、章节划分）
- **内容模块**（正文、练习题、答案、解析、说明框等）
- **语言特征**（纯中文 / 中英双语 / 纯英文）

### Step 2：选择模板

| 文档类型 | 模板文件 |
|---------|---------|
| 英语教学辅导材料（教辅、讲义、练习册）| `assets/template-en-edu.js` |
| 通用文档（报告、教案、论文等）| 使用本文档"通用排版规范"章节 |

如为英语教学辅导材料，直接加载并参照 `assets/template-en-edu.js` 中的样式定义。

### Step 3：构建 docx 脚本

在 `/home/claude/` 下创建 `build_doc.js`，基于选定模板写入文档内容。

**写作原则**：
- 来自 pandoc / `.md` 中间稿的字符串：先 `normalizeExtractedText(s)` 再进 `TextRun`（或只用 `engPara`/`cnPara`）
- 绝不用 `\n` 换行——所有换行用独立 `new Paragraph()`
- 绝不用 unicode 符号 `•` 做列表——用 `LevelFormat.BULLET` + numbering config
- 表格必须同时设置 `columnWidths`（表级）和每格 `width`（单元格级），均用 `WidthType.DXA`
- 表格着色用 `ShadingType.CLEAR`，不用 `ShadingType.SOLID`（否则背景变黑）

### Step 4：生成并验证

```bash
node /home/claude/build_doc.js

python3 /mnt/skills/public/docx/scripts/office/validate.py /home/claude/output.docx
```

验证通过后复制到输出目录：

```bash
cp /home/claude/output.docx /mnt/user-data/outputs/<文档名>_排版版.docx
```

### Step 5：附录——知识点/规则总结（必做）

排版完成后，对原文档内容进行理解与提炼，在文档末尾追加"附录"章节，内容要求：

- 提炼文档中出现的**核心规律**、**重要规则**、**易混淆概念**
- 以**结构化表格**或**规则框**呈现（不做流水文字堆砌）
- 附录标题层级与正文章节同级
- 附录内容必须忠实于原文，不添加原文没有的知识

**附录类型示例**（根据文档类型选取合适的）：

| 文档类型 | 附录内容建议 |
|---------|------------|
| 英语教辅 | 不规则动词表、词形变化规则、语法规则总结 |
| 数学讲义 | 公式汇总、定理列表、易错题型对比 |
| 历史教案 | 时间轴、重要概念对比表 |
| 通用报告 | 关键术语表、核心结论速查 |

---

## 通用排版规范

当无专用模板时，遵循以下出版印刷标准：

### 页面设置

```javascript
properties: {
  page: {
    size: { width: 11906, height: 16838 },  // A4（DXA）
    margin: { top: 1134, right: 1134, bottom: 1134, left: 1440 },  // 上下右 2cm，左 2.54cm
  }
}
```

### 字体体系

| 用途 | 中文字体 | 英文字体 | 字号（DXA half-points）|
|-----|---------|---------|----------------------|
| 书名/大标题 | 黑体 | Times New Roman | 44–52（22–26pt）|
| 章节标题 | 微软雅黑 | Times New Roman | 28–32（14–16pt）|
| 小节标题 | 微软雅黑 | Times New Roman | 24（12pt，粗体）|
| 正文 | 宋体 | Times New Roman | 22（11pt）|
| 注释/页眉页脚 | 宋体 | Times New Roman | 18–20（9–10pt）|

### 颜色系统（十六进制）

```
主色（标题/边框）：#1A3A5C（深蓝）
次色（章节）：    #2E6B9E（中蓝）
正文：           #1A1A1A（近黑）
注释/说明：       #555555（中灰）
答案/要点：       #006400（深绿）
提示/警示：       #8B0000（深红）
规则框：         #8B4513（棕色）
```

### 段落间距

```javascript
// 正文段落
spacing: { before: 80, after: 80, line: 276 }  // 1.15 倍行距

// 章节后
spacing: { before: 200, after: 120 }

// 紧凑段落（答案列表等）
spacing: { before: 40, after: 40 }
```

### 页眉页脚

```javascript
// 页眉：书名（左） + 节标题（右），下方细横线
// 页脚：居中页码，上方细横线
```

### 视觉模块设计

使用"带色块边框的表格"替代普通文字块，区分不同内容类型：

| 内容类型 | 左边框 | 背景色 | 用途 |
|---------|-------|-------|-----|
| 提示语/说明 | 深红色粗线 | 米黄 #FFF8DC | 操作提示、练习说明 |
| 答案 | 绿色边框 | 浅绿 #F0FFF0 | 标准答案 |
| 解析 | 灰色边框 | 白色 | 分析说明 |
| 语法规则 | 棕色粗线 | 浅橙 #FFF9F0 | 规则总结框 |
| 章节标题块 | 蓝色粗线 | 浅蓝 #EBF3FB | 章节入口 |

---

## 与 docx skill 的关系

本 skill 专注于"出版级排版"决策层（样式、结构、模板选择、附录生成）。底层 docx 文件操作细节（XML 结构、tracked changes、图片嵌入等）请参阅 `/mnt/skills/public/docx/SKILL.md`。

两者配合使用：本 skill 决定"排什么"和"怎么排"，docx skill 解决"怎么写代码"。

---

## 快速检查清单

排版完成前，逐项确认：

- [ ] 页面尺寸已显式设置（A4 或 Letter）
- [ ] 页眉 + 页脚已添加（含页码）
- [ ] 标题层级清晰（至少 H1/H2，有 outlineLevel）
- [ ] 正文字体中英文分别指定
- [ ] 表格有 columnWidths + 每格 width（均为 DXA）
- [ ] 无 `\n` 换行、无 unicode 手动项目符号
- [ ] 填空处无可见反斜杠（已 `normalizeExtractedText`，未误删 `___`）
- [ ] validate.py 验证通过
- [ ] 附录章节已生成（知识点/规则总结）
- [ ] 输出文件已复制到 /mnt/user-data/outputs/