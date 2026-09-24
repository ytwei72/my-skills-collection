# md-to-word 参考

视觉常量在 `scripts/md_to_docx.py` 顶部。

## 配色

| 常量 | 值 | 用途 |
|------|----|------|
| `NAVY` | `#1B3A4B` | 章标题、表头、加粗强调 |
| `TEAL` | `#2A6F7F` | 节标题、链接、列表符号、页眉线 |
| `ORANGE` | `#C45C26` | 章标题左侧色条、代码块色条 |
| `BODY` | `#2C3338` | 正文 |
| `MUTED` | `#5B6770` | 图注、来源、页码 |
| `FILL_ICE` | `#E8F1F4` | 章标题底、斑马纹 |
| `FILL_SAND` | `#F7F4EE` | 结论行、代码底 |
| `FILL_MINT` | `#EEF6F3` | 引用底 |
| `LINE` | `#C5D5DC` | 表格边框 |

字体：`FONT=微软雅黑`，`FONT_MONO=Consolas`。

## 大纲映射

`report_mode`：恰好 1 个 `#` 且至少 2 个 `##`。

| 源 | 方案稿（report） | 普通稿 |
|----|------------------|--------|
| `#` | 封面，不进导航 | 标题 1 |
| `##` | 标题 1 | 标题 2 |
| `###` | 标题 2 | 标题 3 |
| `####` | 标题 3 | 标题 4 |

标题段落禁止放进 `w:tbl`。段落底纹 `w:shd`、左边框 `w:pBdr/w:left` 用来做色条。样式上写 `w:outlineLvl`（标题 1 为 0，标题 2 为 1）。

## 列宽

`compute_col_widths`：CJK 计 2，单列上限 `cap_units=32`，最小约 2.15 cm，再缩放到正文宽度。图片表各列等分。

结论行：首格去掉标记后属于 `HIGHLIGHT`（判定、对本方案、相对按键型、结论、合计等）时整行 `FILL_SAND`。

## 命令

```bash
python scripts/md_to_docx.py 需求文档.md
python scripts/md_to_docx.py 需求文档.md D:\out\需求文档.docx
```

生成后可用 lxml 检查：`Heading1` / `Heading2` 的父级链上没有 `tbl`。
