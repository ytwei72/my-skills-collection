# my-skills-collection

跨项目共享的 Cursor Agent Skills 库。通过目录 Junction 链入各业务项目的 `.cursor/skills/`，`git pull` 本库即可同步，无需再拷贝。

## 当前 Skill 清单

| Skill | 说明 |
|-------|------|
| `md-to-rich-html` | Markdown 等 → 单文件富表现 HTML |
| `md-to-html-slides` | Markdown → 单文件 HTML 翻页演示稿（`.slides.html`） |
| `edu-typeset-skill` | 文档出版排版与格式规范化 |
| `drawio-skill` | Draw.io 图表生成与编辑 |
| `feishu-doc-reader` | 飞书文档读取 |
| `feishu-doc-writer` | 飞书文档写入/覆盖 |
| `git-commit-push` | Git 提交与推送辅助 |
| `html-pdf-studio` | HTML → PDF 导出 |
| `md-to-agent-response-html` | Agent 回复摘要卡 + 详情双页 HTML |

> **不包含** `patent-*` 开头技能——各项目自行维护。

## 目录结构

```text
my-skills-collection/
├── md-to-rich-html/
├── md-to-html-slides/
├── edu-typeset-skill/
├── drawio-skill/
├── feishu-doc-reader/
├── feishu-doc-writer/
├── git-commit-push/
├── html-pdf-studio/
├── md-to-agent-response-html/
├── manifests/
│   ├── DocsRep.json
│   └── patent_management.json
└── scripts/
    └── install-project-skills.ps1
```

## 首次安装（每台机器一次）

```powershell
# 1. 克隆本库（若尚未克隆）
git clone <本库 URL> E:\Develop\AI-Agents\my-skills-collection

# 2. 为各项目创建 Junction
Set-Location E:\Develop\AI-Agents\my-skills-collection
.\scripts\install-project-skills.ps1 -Project DocsRep
.\scripts\install-project-skills.ps1 -Project patent_management
```

## 日常更新

```powershell
cd E:\Develop\AI-Agents\my-skills-collection
git pull
# 已安装的 Junction 自动指向新内容，无需再跑 install
```

新增 Skill 时：在本库新建目录 → 更新 `manifests/*.json` → 再执行一次 `install-project-skills.ps1`。

## 业务项目 Git 约定

- **不要**把 Junction 目录提交进 DocsRep / patent_management 的 Git。
- 各项目 `.gitignore` 已忽略本库链接的 skill 目录。
- 克隆业务项目后须执行上方 install 脚本。

## 修改 manifest 中的项目路径

编辑 `manifests/DocsRep.json` 或 `manifests/patent_management.json` 中的 `projectRoot` 字段。
