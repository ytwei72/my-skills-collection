# pkg-disk-usage

查看当前 Python 环境里**哪些已安装包最占磁盘**，按体积从大到小排名，并给出总占用。

> **说明**：本文件供**人类**查阅。Agent 仅在用户**明确点名**本 skill 时加载 `SKILL.md`。

---

## 如何触发

本 skill 须**点名**才会加载，例如：

- `/pkg-disk-usage`
- `@pkg-disk-usage`
- 「用 pkg-disk-usage 技能…」
- 「按 pkg-disk-usage 统计包体积」

未点名时 Agent 不会自动启用本技能。

---

## 自然语言命令示例

### 快速查看：谁最占空间

```
用 pkg-disk-usage 看看当前 venv 里哪些包最大
```

```
/pkg-disk-usage 统计一下已安装包的磁盘占用
```

```
这个项目虚拟环境里，前 20 个最大的包是哪些？
```

### 指定显示数量

```
用 pkg-disk-usage 列出占用最大的 100 个包
```

```
只看前 10 名，告诉我谁最占磁盘
```

### 导出结果

```
用 pkg-disk-usage 统计包体积，导出到 package_sizes.csv
```

```
把前 50 个最大包排名导出成 CSV，文件名 top50_packages.csv
```

### 指定要统计的环境

```
用 pkg-disk-usage 统计本项目 .venv 的包占用
```

```
统计全局 Python 3.12 环境里安装的包体积（不要用项目 venv）
```

```
我激活了 conda 环境 ml，用 pkg-disk-usage 统计这个环境
```

### 排查与决策

```
用 pkg-disk-usage 看看 torch 占了多少空间
```

```
哪些依赖加起来超过 100MB？帮我排个名
```

```
想瘦身 venv，用 pkg-disk-usage 找出最值得卸载的大包
```

```
对比一下：当前环境一共装了多少包、总共占多少磁盘
```

---

## 你会得到什么

Agent 运行后会汇报类似内容：

- 当前统计的 `site-packages` 路径
- 排名表：包名、版本、可读大小（如 `4.37 GB`、`137.72 MB`）
- 汇总：共多少个包、总占用多少

若你要求导出，还会给出 CSV 文件路径。

---

## 说法提示

| 你想做的事 | 可以这样说 |
|-----------|-----------|
| 默认排名（前 50） | 「统计包体积」「哪些包最大」 |
| 改数量 | 「前 100 个」「只看前 10」 |
| 导出表格 | 「导出 CSV」「保存成 Excel 能打开的表」 |
| 指定环境 | 「用项目 .venv」「用全局 Python」「用当前 conda 环境」 |
| 找某个包 | 「torch 占多少」「xx 包有多大」 |

---

## 与其他 skill 的边界

| 需求 | 说明 |
|------|------|
| 查**已安装包**占磁盘 | 用本 skill |
| 查**整个磁盘/文件夹**占用 | 不用本 skill，直接让 Agent 分析目录 |
| 查**依赖关系/为什么装了某包** | 用 `pip show` / `pipdeptree` 等，本 skill 只做体积排名 |

Agent 执行细节见 [SKILL.md](SKILL.md)。

---

## 在新项目中挂载本 Skill（目录 Junction）

本 skill 放在共享库 `my-skills-collection` 里，不必拷贝进业务项目。在目标项目的 `.cursor/skills/` 下建一个指向本目录的 **Junction**（Windows 目录联接）即可；`git pull` 共享库后，各项目自动用到最新内容。

推荐在 Cursor 里用自然语言让 Agent 创建链接（把路径换成你本机实际路径）。

### 推荐说法（复制后改路径）

```
在当前项目的 .cursor/skills 目录下，用目录 Junction 挂载共享 skill：
链接名 pkg-disk-usage，目标指向
D:\Develop\my-skills-collection\pkg-disk-usage。
若 .cursor\skills 不存在就先创建；若已有同名真实目录先别删，告诉我；
若已有指向别处的 Junction 则先删再建。不要把 Junction 提交进 Git。
```

一次挂多个 skill 时可以说：

```
把 D:\Develop\my-skills-collection 里的这些 skill
用 Junction 链到本项目 .cursor\skills\ 下（同名目录）：
pkg-disk-usage、git-commit-push、md-to-rich-html。
路径按本机实际位置调整；已存在且指向正确的跳过；
不要提交这些链接。
```

### 等价的 PowerShell（自己执行时）

```powershell
$skillsDir = "D:\path\to\YourProject\.cursor\skills"
$libSkill  = "D:\Develop\my-skills-collection\pkg-disk-usage"
New-Item -ItemType Directory -Force -Path $skillsDir | Out-Null
New-Item -ItemType Junction -Path (Join-Path $skillsDir "pkg-disk-usage") -Target $libSkill
```

### 注意

- Junction 目标必须是本机上的绝对路径；换电脑时在那台机器上再挂一次即可。
- 业务项目 `.gitignore` 应忽略这些链接目录，避免把共享 skill 误提交进项目仓库。
