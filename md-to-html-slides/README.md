# md-to-html-slides

把 Markdown 转成**单文件 HTML 翻页演示稿**（`.slides.html`）：双击即放映、离线可用、可 Ctrl+P 打印 PDF。

> **说明**：本文件供**人类**查阅。Agent 仅在用户**明确点名**本 skill 时加载 `SKILL.md`；执行转换任务时不应依赖本文。

---

## 如何触发

本 skill 设置了 `disable-model-invocation: true`，**必须点名**才会加载，例如：

- `/md-to-html-slides`
- `@md-to-html-slides`
- 「使用 md-to-html-slides 技能」
- 「按 md-to-html-slides 转成幻灯片」

### 容易匹配的说法

| 意图 | 示例 |
|---|---|
| MD → 演示稿 | 把这份 md 做成 HTML 幻灯片 / web 版 PPT / slides |
| 离线放映 | 单文件演示稿、浏览器翻页、能打印 PDF |
| 明确边界 | 不要 pptx，要 HTML 演示稿 |

### 通常应改用其他 skill 的情况

| 需求 | 改用 |
|---|---|
| 长滚动富文本网页 | `md-to-rich-html` |
| 真 `.pptx`、PowerPoint 可编辑、原生动画 | `ppt-master` |
| 摘要卡 + 详情双页 | `md-to-agent-response-html` |
| 只有主题、没有源 MD | 先提供 `.md`，或走 `ppt-master` topic-research |

---

## 输入与输出

| 项目 | 说明 |
|---|---|
| **输入** | 仅 `.md` / `.markdown`；多文件按顺序合并；目录扫描需确认顺序 |
| **输出** | `<源文件名>.slides.html`，与源文件同目录（除非指定路径） |
| **画布** | 默认 16:9（1920×1080）；可说「4:3」切 1440×1080 |
| **依赖** | 零外链、零 CDN；图片 base64 内联 |

---

## 主题与配色

### 默认：三种主题 + 运行时切换

生成物默认内置 **3 套清新配色**，放映时可切换：

| id | 名称 | 说明 |
|---|---|---|
| `aqua` | 青蓝 | 默认起始主题 |
| `azure` | 晴空 | 蓝系 |
| `violet` | 雅紫 | 紫粉系 |

**操作**：右下角 **◐** 按钮，或键盘 **T** 循环切换；选择会记住（`localStorage`）。

### 指令：关闭主题切换（单一配色）

在请求里加上任一说法即可：

```
把 report.md 转成 slides，关闭主题切换
不要主题 / 单一配色 / 固定配色 / 不要换肤
```

效果：只保留一套配色（默认青蓝），**无**切换按钮与 **T** 快捷键。

### 指令：指定某一主题

锁定为单一主题（同样无切换器）：

```
用晴空主题把 intro.md 做成幻灯片
指定主题 azure
默认雅紫配色
theme: violet
```

中文名与 id 均可：`青蓝/aqua`、`晴空/azure`、`雅紫/violet`。

### 指令：多主题但改默认起始

保留 3 主题切换，但打开时从指定主题开始：

```
3 主题，默认从晴空开始
多主题，起始用 violet
```

### 指令：整包视觉模板

与内置 3 主题不同，这是**整 deck 风格包**（含装饰与色板），来自 `templates/ppt-layouts/`：

```
用 dark_tech 模板做技术分享 slides
走 minimal_business 风格
modern_academic 模板转 md
```

可选模板：`dark_tech`（深色科技）、`minimal_business`（极简商务）、`modern_academic`（现代学术）。

---

## 用户指令示例

### 1. 最简转换

```
/md-to-html-slides
把 PlatformSystem/AiBusinessAssistant/2026-06-19-ai-product-catalog-design.md 转成 HTML 演示稿
```

### 2. 带比例与主题

```
用 md-to-html-slides 把 deck.md 做成 4:3 幻灯片，关闭主题切换
```

```
把 pitch.md 转 slides，指定主题 azure，要演讲者备注
```

### 3. 多文件合并

```
按顺序合并 part1.md part2.md part3.md，做成一份 slides，3 主题默认从青蓝开始
```

### 4. 高质量版面（对标样板）

```
用 md-to-html-slides 转换 catalog.md，版面质量不低于 ai-product-catalog-slides-v1.html，多用卡片和架构图
```

### 5. 与 pptx 的边界

```
这份 md 先做 HTML 演示稿（不要 pptx），要能 F 全屏和 Ctrl+P 打 PDF
```

若需要可在 PowerPoint 里改动的 `.pptx`，请改用 **ppt-master**。

---

## 放映快捷键

| 键 | 功能 |
|---|---|
| ← / → / Space | 翻页 |
| F | 全屏 |
| O | 缩略图概览 |
| S | 演讲者视图（备注 + 计时） |
| T | 切换主题（**仅默认多主题模式**） |
| B | 黑屏 |
| ? | 快捷键提示 |
| Ctrl+P | 打印 PDF（需勾选「打印背景图形」） |

---

## 版本与模板体系

本 skill 按四层演进，详见 `SKILL.md` §版本计划：

1. **样式（Style）** — 主题色、字体、阴影；当前 3 内置主题
2. **组件（Component）** — 卡片、KPI、对比条、架构图、流程图等（见 `reference.md` §高质量组件库）
3. **版面（Layout）** — 封面、章节、双栏、表格等 `data-layout` 页型
4. **模板（Template）** — `templates/ppt-layouts/` 整包视觉规范

质量基准样板：`PlatformSystem/AiBusinessAssistant/ai-product-catalog-slides-v1.html`。

---

## 文件说明

| 文件 | 读者 | 内容 |
|---|---|---|
| `README.md` | 人类 | 本文件：触发方式、主题指令、示例 |
| `SKILL.md` | Agent（点名后） | 完整规范：切片规则、质量硬标准、工作流程 |
| `reference.md` | Agent（按需） | HTML/CSS/JS 骨架、组件库、主题实现细节 |

---

## 常见问题

**Q：为什么没有自动加载？**  
A：本 skill 须明确点名；说「做成 PPT」且未点名时，Agent 可能先问你要 `.pptx` 还是 HTML slides。

**Q：能转 PowerPoint 吗？**  
A：当前交付 HTML；真 `.pptx` 请用 ppt-master。后续计划有 `toolkits/html_slides_to_pptx/`（截图保真）。

**Q：打印 PDF 没有背景色？**  
A：浏览器打印对话框勾选「背景图形」/「Background graphics」。

**Q：内容太多一页挤不下？**  
A：skill 会切页或精简，**不会**把字号缩到不可读；可主动要求「拆成更多页」。
