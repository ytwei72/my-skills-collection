---
name: bump-version
disable-model-invocation: true
description: >-
  递增本仓库系统版本号（VERSION / BUILD）并同步前后端常量。点名即授权按
  git-commit-push：先提交推送已有代码变更，再改版本并再提交推送。
  默认只把 BUILD +1；可指定大版本 / 小版本 / 补丁 +1，或写成指定 X.Y.Z。
  仅在用户明确点名时加载（/bump-version、bump-version 技能、升构建号并提交推送等）。
  未点名时不要读取本技能。不必先单独跑 git-commit-push。
---

# 版本号递增并推送

改本仓库内嵌的系统版本（`VERSION` + `BUILD`），并**一步做完**原先的两步：
`git-commit-push`（已有代码）→ 升版本 → 再 `git-commit-push`（版本文件）。
**不是**写 changelog / 用户指南；那是 `release-docs`。

## 何时启用

**仅**在用户**明确**点名时执行，例如：

- `/bump-version`
- `/bump-version 小版本`
- `/bump-version 1.0.0`
- 「用 bump-version 技能…」「升一下构建号并提交推送」

未点名时不要读取本文件，也不要因为「改完代码」就自动升版本。
点名本技能 = 已授权 commit + push，**不必**再先跑一遍 `git-commit-push`。

## 总原则

- 本仓库 **Windows + PowerShell**：不用 Bash/WSL；路径用 `E:\...`；串联用 `;`。
- **不要**为验证跑 build / compile / 前端打包。
- 版本源是代码常量，不读数据库、不读环境变量。
- `BUILD` 只增不减；省略时 **当前值 +1**。
- 先提交已有代码，再改版本号，再提交版本文件（两次提交）。不要把功能改动和版本号揉进同一次 commit。
- 两次提交都按 [git-commit-push](../git-commit-push/SKILL.md) 执行；默认每次 commit 后都 push。不要只改数字就结束，也不要让用户再说一声才 push。
- 用户原话明确「只改版本 / 先别提交 / 先别推」时，按该例外停在对应步骤，并在回报里说明。

## 0. 加载 git 约定

先 **Read** `.cursor/skills/git-commit-push/SKILL.md`（一次即可）。
该 Junction 不存在时：仍按约定式提交、禁止 `git add .` / `-A`、禁止 skip hooks、默认 push；用户明确「先别推」则只 commit。

版本专用路径（**不要**放进第 1 次提交）：

- `app/core/app_version.py`
- `frontend/src/config/appVersion.ts`

`pyproject.toml`、`frontend/package.json`、`frontend/package-lock.json` 若除版本字段外还有本次相关改动，放进第 1 次提交；升 `VERSION` 后脚本再改它们，余下 diff 归第 2 次提交。

## 1. 解析意图

先读 `app/core/app_version.py` 的 `VERSION`、`BUILD`，再按下表选脚本参数。

| 用户原话 | 脚本参数 | 结果 |
|----------|----------|------|
| 裸 `/bump-version`，或只说升构建号 / build | （无额外参数） | `VERSION` 不变，`BUILD +1` |
| 大版本 / major / 升大版本 | `--major` | `X.Y.Z` → `(X+1).0.0`，`BUILD +1` |
| 小版本 / minor / 升小版本 | `--minor` | `X.Y.Z` → `X.(Y+1).0`，`BUILD +1` |
| 补丁 / patch / 修订号 | `--patch` | `X.Y.Z` → `X.Y.(Z+1)`，`BUILD +1` |
| 指定 `X.Y.Z`（如 `0.9.0`、`1.0.0`） | `--set X.Y.Z` | 写成该版本，`BUILD +1` |
| 同时指定构建号（如 `build 200`、`0.9.0 (200)`） | 加上 `--build N` | `BUILD` 写成 `N`（必须 `> 当前值`） |

多种说法冲突时以**更具体**的为准（指定版本号 > 大小版本 > 默认 build）。
指定版本必须是 `X.Y.Z`。不要猜预发布后缀（`1.0.0-rc.1` 等），用户没写就不要加。

## 2. 先提交已有代码（原 git-commit-push）

在改版本文件**之前**：

1. 按 git-commit-push §1 摸清工作区（`status` / `diff` / `log`）。
2. 若存在与本次会话相关、且**不是**版本专用路径的改动：按 git-commit-push §3 提交它们（约定式提交，type/scope 跟功能走），再按 §4–§5 默认 push。
3. 工作区已干净、或只剩无关/未授权文件：跳过本步，不要空 commit。
4. 不要把密钥、日志、`data/`、`__pycache__` 加进去。
5. 本步 commit 失败则**停**，不要升版本。push 失败：说明错误，仍可继续升版本；第 4 步会再尝试 push。

用户明确「只改号 / 先别提交」：跳过本步与第 4 步。

## 3. 改版本文件

在**业务仓库根目录**执行（只跑这一条，不要手改数字）。脚本在共享库，经 Junction 暴露为下面这条路径：

```powershell
uv run python .cursor/skills/bump-version/scripts/bump.py
```

按 §1 追加参数，例如：

```powershell
uv run python .cursor/skills/bump-version/scripts/bump.py --minor
uv run python .cursor/skills/bump-version/scripts/bump.py --major
uv run python .cursor/skills/bump-version/scripts/bump.py --set 1.0.0
uv run python .cursor/skills/bump-version/scripts/bump.py --set 0.9.0 --build 200
```

脚本按 cwd / `git rev-parse --show-toplevel` 找仓库根，**不要**按脚本文件路径往上数。

脚本会改这些文件（`VERSION` 没变时后三项不动）：

| 文件 | 字段 |
|------|------|
| `app/core/app_version.py` | `VERSION`、`BUILD`（源头） |
| `frontend/src/config/appVersion.ts` | `APP_VERSION`、`APP_BUILD`（必须与源头一致） |
| `pyproject.toml` | `[project].version`（仅 `VERSION` 变化时） |
| `frontend/package.json` | 顶层 `version`（仅 `VERSION` 变化时） |
| `frontend/package-lock.json` | 仅当其 `version` 等于旧 `VERSION` 时一并改 |

脚本打印 `旧 -> 新` 和 `updated:` 列表。失败则停，不要手工补改一半。
不要改其它文件里的版本字面量（依赖包、第三方 API 的 `X-TC-Version` 等）。

## 4. 再提交版本文件

版本文件改成功后，再走一遍 git-commit-push（默认 commit + push）：

1. **必须**只 stage 脚本列出的版本文件（外加本次会话里随版本一起改的、尚未提交的相关文件）。
2. 提交说明聚焦版本变化：

```powershell
$msg = @'
chore(version): 构建号 132 → 133

体验/验证环境靠内嵌 BUILD 区分实例，发版前递增构建号。
'@
```

`VERSION` 也变了时，header 写成 `chore(version): 发布 0.9.0 (133)`。
第 2 步已经把功能改动单独提交过，这里不要再写成功能 type。

3. 默认 push。用户明确「先别推」则两次都只 commit。

## 5. 回报

结束时说明：

- 第 2 步：是否提交了已有代码（hash / 跳过原因）、是否已 push
- 旧版本 → 新版本（`VERSION` + `BUILD`）
- 改了哪些版本文件
- 版本提交：分支、commit hash、是否已 push、与远端关系

**禁止**改完版本后说「若要提交/推送可以说一声」。
**禁止**让用户再补一句 `/git-commit-push` 才去提交已有代码。

## 示例

**用户**：`/bump-version`（工作区有本次功能改动）

1. 按 git-commit-push 提交并推送这些改动
2. 跑脚本（无参数）→ `BUILD +1`
3. 再提交版本文件并 push

**用户**：`/bump-version`（工作区已干净）

1. 跳过第 2 步
2. `BUILD +1` → 提交版本文件并 push

**用户**：`/bump-version 小版本`

1. 先提交已有代码（若有）
2. `--minor` → 例如 `0.8.0 (132)` → `0.9.0 (133)`
3. 同步 `pyproject.toml`、`frontend/package.json`
4. 提交版本文件并 push

**用户**：`/bump-version 1.0.0`

1. 先提交已有代码（若有）
2. `--set 1.0.0` → `1.0.0`，`BUILD +1`
3. 提交版本文件并 push

**用户**：`/bump-version 只改号，先别提交`

1. 不要提交已有代码，也不要提交版本文件
2. 按意图改版本，回报未提交
