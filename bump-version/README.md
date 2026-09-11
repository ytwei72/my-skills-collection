# bump-version

递增业务仓库内嵌的系统版本（`VERSION` / `BUILD`），同步前后端常量，并**一步做完**原先的两步：先按 `git-commit-push` 提交推送已有代码，再升版本并再提交推送。

适用于与 `remote-sensing-monitor` / `clip-agent` 相同的版本文件布局（`app/core/app_version.py` + 前端 `appVersion.ts`）。

> **说明**：本文件供**人类**查阅。Agent 仅在用户**明确点名**本 skill 时加载 `SKILL.md`。

---

## 如何触发

须**点名**才会加载，例如：

- `/bump-version` —— 默认只把 **BUILD +1**（有未提交的相关代码时会先提交推送）
- `/bump-version 小版本` / `/bump-version 大版本` / `/bump-version 0.9.0`
- `@bump-version`、「用 bump-version 技能升构建号并推送」

未点名时 Agent 不会自动升版本。**不必**再先单独跑一遍 `git-commit-push`。

---

## 版本存在哪

| 文件 | 作用 |
|------|------|
| `app/core/app_version.py` | 源头：`VERSION`、`BUILD` |
| `frontend/src/config/appVersion.ts` | 前端常量，必须与源头一致 |
| `pyproject.toml`、`frontend/package.json` | 仅 `VERSION`（X.Y.Z）变化时同步 |

`BUILD` 是单调递增的构建号，用来区分体验环境与版本验证环境各自带的是哪一包。

---

## 常用说法

```
/bump-version
/bump-version 小版本
/bump-version 大版本
/bump-version 1.0.0
/bump-version 只改号，先别提交
```

---

## 在新项目中挂载本 Skill（目录 Junction）

本 skill 放在共享库 `my-skills-collection` 里，不必拷贝进业务项目。目标项目还需同时挂载 `git-commit-push`（本技能会 Read 它的约定）。

```
把 E:\Develop\AI-Agents\my-skills-collection 里的 bump-version、git-commit-push
用 Junction 链到本项目 .cursor\skills\ 下（同名目录）。
若 .cursor\skills 不存在就先创建；已存在且指向正确的跳过；
若已有指向别处的 Junction 则先删再建；若已有同名真实目录先别删，告诉我。
不要把这些 Junction 提交进 Git。
```

等价 PowerShell：

```powershell
$libRoot   = "E:\Develop\AI-Agents\my-skills-collection"  # 按本机路径调整
$skillsDir = "E:\path\to\YourProject\.cursor\skills"
foreach ($name in @("bump-version", "git-commit-push")) {
    $link = Join-Path $skillsDir $name
    if (Test-Path $link) { continue }
    New-Item -ItemType Junction -Path $link -Target (Join-Path $libRoot $name) | Out-Null
}
```
