# drawio-skill（本仓库）

本目录为 [drawio-skill](https://github.com/Agents365-ai/drawio-skill) 的本地副本，供 Cursor Agent 在用户**显式要求**使用 `drawio-skill` / `draw.io` 时加载。完整工作流见 [`SKILL.md`](SKILL.md)。

---

## 本机 draw.io CLI 路径（Windows）

本仓库开发机将 draw.io 安装在 **D 盘**，导出命令须使用下列路径（勿默认 `C:\Program Files\draw.io\`）：

```powershell
$DRAWIO = "D:\Program Files\draw.io\draw.io.exe"

# 检查版本
& $DRAWIO --version

# 预览 PNG（自检用，不加 -e，限制宽度）
& $DRAWIO -x -f png --width 2000 -b 10 -o "输出.png" "输入.drawio"

# 最终 PNG（可嵌入 XML，便于再编辑）
& $DRAWIO -x -f png -e -s 2 -b 10 -o "输出.drawio.png" "输入.drawio"
# 若 vision/严格解码报错，可对 -e 的 PNG 运行：
# .venv\Scripts\python.exe scripts\repair_png.py 输出.drawio.png
```

Agent 在本仓库执行 draw.io 相关 Shell 时，应优先使用 `$DRAWIO` 上述路径。

---

## 仓库内绘图示例：图1 系统结构框图

### 产出文件

| 文件 | 说明 |
|------|------|
| [`docs/图1-系统结构框图.drawio`](../../../docs/图1-系统结构框图.drawio) | 可编辑源图 |
| [`docs/图1-系统结构框图.png`](../../../docs/图1-系统结构框图.png) | 预览/文档引用 PNG |
| [`docs/图1-系统结构框图.drawio.png`](../../../docs/图1-系统结构框图.drawio.png) | 嵌入 diagram XML 的高清 PNG |

### 画图描述的出处（须与交底书一致）

本示例对应专利交底书 **「一种面向异构集群的批任务资源感知调度与限频重排队方法及系统」** 中的 **图1**，描述来源如下：

| 优先级 | 路径 | 章节 / 内容 |
|--------|------|-------------|
| 主文档 | `patent_case_files/disclosure_generation/223666b4-f2f9-4bad-a3e8-35b19a4b184a/agent_run/8a5f63c84565/一种面向异构集群的批任务资源感知调度与限频重排队方法及系统_20260602202438.md` | **§3.2 系统框图**（图1 总体架构）、**§3.3 模块功能说明**（模块（4）～（8）及「模块关联关系」段落） |
| 布局与连线规范 | `.cursor/skills/patent-drawing-figures/SKILL.md` | **§1.3** 系统框图规范；**§3.3.1～§3.3.3**（含「异构批任务调度系统（图1）推荐拓扑模板」） |
| 图类型预设 | `.cursor/skills/drawio-skill/references/diagram-types.md` | **Architecture** 小节（swimlane、服务框、队列样式等） |

交底书 md 内原引用路径为 `figures/图1-系统结构框图.png`（相对 agent_run 目录）；本示例另在仓库根下 **`docs/`** 保留一份，便于技能说明与跨案件复用。

### 示例图内容摘要

- **图名**：图1　系统结构框图（批任务调度系统总体架构）
- **分层（自上而下）**：用户与配置层 → 全局队列 → 调度核心处理链（4→5→6）→ 执行与可靠性（7、8 可选）→ 异构工作节点（9、10、11）
- **附图标记**：组件框内为「名称 +（N）」交底书阶段写法（见 `patent-drawing-figures` §四）
- **线型**：实线主数据/控制流；虚线配置下发与假死反馈；点划线指标上报与心跳；底部图例说明

### 一键重新导出（PowerShell）

在仓库根目录执行：

```powershell
Set-Location "E:\Develop\AI-Agents\patent_management"
$DRAWIO = "D:\Program Files\draw.io\draw.io.exe"
$src = "docs\图1-系统结构框图.drawio"
& $DRAWIO -x -f png --width 2000 -b 10 -o "docs\图1-系统结构框图.png" $src
& $DRAWIO -x -f png -e -s 2 -b 10 -o "docs\图1-系统结构框图.drawio.png" $src
```

修改布局时编辑 `docs/图1-系统结构框图.drawio`，再运行上述命令即可。

---

## 与本示例相关的 Agent 指令模板

向 Agent 发起绘图时可显式写明（路径按实际案件替换）：

```
请使用 drawio-skill 绘制专利交底书图1（系统结构框图）。
- CLI：D:\Program Files\draw.io\draw.io.exe
- 描述出处：<交底书 md> §3.2、§3.3；patent-drawing-figures §3.3.3；diagram-types Architecture
- 输出：docs/图1-系统结构框图.drawio 与 .png
```

更完整的模块清单、边列表与分层约束，见本仓库对话中生成的 drawio-skill 指令（或从上述 §3.2 / §3.3 / `patent-drawing-figures` §3.3.3 自行整理）。

---

## 目录说明

| 路径 | 用途 |
|------|------|
| `SKILL.md` | Agent 主技能与工作流 |
| `references/` | 图类型、形状、样式、排错等 |
| `scripts/` | 校验、自动布局、PNG 修复、URL 编码等 |
| `styles/built-in/` | 内置样式预设 JSON |

上游项目：<https://github.com/Agents365-ai/drawio-skill>（本 README 中的示例与 D 盘路径为 **patent_management 仓库本地约定**，非上游默认配置）。
