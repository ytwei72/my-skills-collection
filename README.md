# my-skills-collection

跨项目共享的 Cursor Agent Skills 库。通过目录 Junction 链入各业务项目的 `.cursor/skills/`，`git pull` 本库即可同步，无需再拷贝。

## 当前 Skill 清单

| Skill | 说明 |
|-------|------|
| `md-to-rich-html` | Markdown 等 → 单文件富表现 HTML |
| `md-to-word` | Markdown → 规范美观的 Word(.docx)，表格列宽内容自适应 |
| `md-to-html-slides` | Markdown → 单文件 HTML 翻页演示稿（`.slides.html`） |
| `edu-typeset-skill` | 文档出版排版与格式规范化 |
| `drawio-skill` | Draw.io 图表生成与编辑 |
| `feishu-doc-reader` | 飞书文档读取 |
| `feishu-doc-writer` | 飞书文档写入/覆盖 |
| `bump-version` | 递增 VERSION / BUILD；一步完成「提交已有代码 + 升版本 + 再提交推送」 |
| `git-commit-push` | Git 提交与推送辅助 |
| `html-pdf-studio` | HTML → PDF 导出 |
| `md-to-agent-response-html` | Agent 回复摘要卡 + 详情双页 HTML |
| `pkg-disk-usage` | 统计当前 Python 环境已安装包的磁盘占用 |
| `weekly-work-summary` | 分模块工作记录 → 工作周报总结（可控字数/格式/输出类型） |
| `meeting-asr` | 会议发言录音 → 带说话人/时间戳的转写文稿（阿里云 NLS） |
| `skill-creator` | 创建、优化并评测 Cursor Agent Skill |

> **不包含** `patent-*` 开头技能——各项目自行维护。

## 目录结构

```text
my-skills-collection/
├── md-to-rich-html/
├── md-to-word/
├── md-to-html-slides/
├── edu-typeset-skill/
├── drawio-skill/
├── feishu-doc-reader/
├── feishu-doc-writer/
├── bump-version/
├── git-commit-push/
├── html-pdf-studio/
├── md-to-agent-response-html/
├── pkg-disk-usage/
├── weekly-work-summary/
├── meeting-asr/
└── skill-creator/
```

## 首次挂载（每台机器、每个业务项目一次）

1. 克隆本库到本机任意路径（各电脑路径可以不同）。
2. 在业务项目里，把需要的 skill 用 **目录 Junction** 链到 `.cursor/skills/<skill名>`，目标指向本库中对应目录。

推荐在 Cursor 里用自然语言让 Agent 创建（把路径换成你本机实际位置）：

```
把 D:\Develop\my-skills-collection 里的这些 skill
用 Junction 链到本项目 .cursor\skills\ 下（同名目录）：
md-to-rich-html、md-to-word、git-commit-push、pkg-disk-usage。
若 .cursor\skills 不存在就先创建；已存在且指向正确的跳过；
若已有指向别处的 Junction 则先删再建；若已有同名真实目录先别删，告诉我。
不要把这些 Junction 提交进 Git。
```

等价 PowerShell 示例：

```powershell
$libRoot   = "D:\Develop\my-skills-collection"   # 本库在本机的路径
$skillsDir = "D:\path\to\YourProject\.cursor\skills"
$names     = @("pkg-disk-usage", "git-commit-push")  # 按需增减

New-Item -ItemType Directory -Force -Path $skillsDir | Out-Null
foreach ($name in $names) {
    $link   = Join-Path $skillsDir $name
    $target = Join-Path $libRoot $name
    if (Test-Path $link) { continue }
    New-Item -ItemType Junction -Path $link -Target $target | Out-Null
}
```

换电脑时：在本机重新挂一次即可（Junction 目标必须是本机绝对路径）。单个 skill 的说明也可参见各 skill 目录下的 `README.md`（例如 `pkg-disk-usage`）。

## 日常更新

```powershell
cd D:\Develop\my-skills-collection   # 按本机路径调整
git pull
# 已挂载的 Junction 自动指向新内容，无需再建链接
```

新增 Skill 时：在本库新建目录 → 在需要用到它的业务项目里再挂一条同名 Junction。

## 业务项目 Git 约定

- **不要**把 Junction 目录提交进业务项目的 Git。
- 各项目 `.gitignore` 应忽略本库链接的 skill 目录。
- 克隆业务项目后，在本机按上方方式重新挂载一次。
