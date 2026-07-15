# md-to-word 参考:可调参数与扩展

脚本 `scripts/md_to_docx.py` 顶部集中了全部视觉常量,改这里即可整体调整风格。

## 配色常量

| 常量 | 默认值 | 用途 |
|------|--------|------|
| `COLOR_PRIMARY` | `#1F497D` 深蓝 | 一级/章节标题、字段列文字 |
| `COLOR_ACCENT` | `#2E74B5` 亮蓝 | 子标题、竖条、列表符号 |
| `COLOR_TEXT` | `#333333` | 正文 |
| `COLOR_MUTED` | `#445566` | 引用/页码/弱化 |
| `COLOR_CODE` | `#A31D11` | 内联代码 |
| `COLOR_LINK` | `#1A5FB4` | 链接文字 |
| `HEX_HEADER` | `1F497D` | 表头填充 |
| `HEX_LABEL` | `DCE6F1` | 字段列填充 |
| `HEX_STRIPE` | `F2F6FB` | 斑马纹 / 引用底纹 |
| `HEX_CODEBG` | `F5F5F5` | 代码块底纹 |
| `HEX_BORDER` | `B7C6D9` | 表格/段落边框 |

## 字体常量

`FONT_HEI=黑体`、`FONT_SONG=宋体`、`FONT_KAI=楷体`、`FONT_MONO=Consolas`。
如目标机无楷体/黑体,可换 `微软雅黑` / `等线` 等系统字体。

## 字号

- `BASE_SIZE=10.5`(正文)、`TABLE_SIZE=10`(表格)。
- 标题字号在各分支内写死:22 / 15 / 12.5 / 11pt,可按需微调。

## 列宽自适应算法(`compute_col_widths`)

- `min_cm=1.4`:单列最小宽度,防止短列被压到不可读。
- `cap_units=52`:单列自然宽度上限(显示单位,CJK=2)。调大 → 长描述列更宽;
  调小 → 各列更均衡。
- 显示宽度 `display_width`:`ord(ch) > 0x2E7F` 记 2,否则记 1(覆盖中日韩与
  全角标点)。
- 分配:`width = max(min_cm, total * nat_c / Σnat)`,再整体缩放回页面可用宽度。
- 固定生效:关闭 `autofit` + 写 `tblGrid` 各 `gridCol` 宽 + `tblLayout=fixed`。

## 字段表识别

当表为 2 列且表头首格 ∈ `{字段, 项目, 项}` 时,判定为「字段/说明」表:
左列高亮加粗居中、右列左对齐。新增触发词可改 `is_field` 判断集合。

## 支持的 Markdown 语法

- 标题 `#`~`####`、段落、`---`/`***` 分隔线(渲染为空隙)。
- 表格(GFM 竖线表)、单元格内 `<br>` 换行。
- 引用 `>`(多行合并)、有序 `1.` / 无序 `-*+` 列表。
- 围栏代码块 ```` ``` ````、内联 `**bold**` `*italic*` `` `code` `` `[text](url)`。
- 图片 `![](path)`:相对路径按源文件目录解析,超宽自动限制到 14cm。

## 未覆盖/降级

- 嵌套列表深度、表格内复杂块、脚注、HTML 富标签等未特殊处理,按纯文本降级。
- 需要公文红头/版记、Word 自动多级编号:改用 `official-doc-formatter`(点名)。
- 需要 PDF:先用本 skill 生成 docx,再用 `html-pdf-studio` 或 Word 导出。

## 命令示例

```bash
# 同目录同名输出
python scripts/md_to_docx.py 需求文档.md

# 指定输出
python scripts/md_to_docx.py 需求文档.md D:\out\需求文档.docx

# 仓库 venv
D:\Develop\DocsRep\.venv\Scripts\python.exe scripts/md_to_docx.py 需求文档.md
```
