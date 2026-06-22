---
name: git-commit-push
disable-model-invocation: true
description: >-
  Git 工作流：在代码修改后提交、推送，以及 pull / merge / rebase / sync 与冲突处理。
  仅在用户明确点名时加载（/git-commit-push、git-commit-push 技能、按该技能提交并推送等）。
  禁止因「改完代码」「保存一下」等泛化表述自动启用；未点名时不要读取本技能。
  启用后默认 commit 并 push；不要只 commit 后让用户再说一声才 push。
---

# Git 提交、推送与同步

## 何时启用

**仅**在用户**明确**要求使用本技能时执行，例如：

- `/git-commit-push`
- 「按 git-commit-push 技能…」
- 「用提交推送技能做 commit + push」

以下**不算**启用本技能（沿用默认规则：不主动 commit/push，除非用户另有明确指令）：

- 「改一下这个 bug」「帮我实现…」
- 「提交吧」但未点名本技能（仍可按对话中的单次明确授权处理，**不要**为此自动 Read 本文件）

启用后，先根据用户原话判断子任务（可组合）：`commit` | `push` | `pull` | `merge` | `sync` | `status`。

## 总原则

- **启用本技能 = 已授权 commit + push（默认）**：用户点名本技能时，视为已明确要求推送到远端；完成 §3 Commit 后**必须**继续 §5 Push，**禁止**只提交后结束，也**禁止**回复「若要推到远端，可以说一声，我执行 git push」之类让用户二次授权的话术。
- **仅 commit、不 push 的例外**：用户原话**明确**只要提交、不要推送（例如「只 commit 不 push」「先别推」）时，做完 §3 即结束，并在回报中说明未推送。
- **没有启用本技能时**：未要求 commit 则不 commit；未要求 push 则不 push；未要求 pull/merge/sync 则不拉取/合并。
- **绝不**改 `git config`；**绝不** `push --force` 到 `main`/`master`（用户明确要求且知悉风险时方可讨论，默认拒绝）。
- **禁止**跳过钩子（`--no-verify` 等）除非用户明确要求。
- **禁止**交互式 git（`-i`：`rebase -i`、`add -i` 等）。
- **禁止**未授权时的破坏性命令：`reset --hard`、`clean -fdx`、强推、删分支、改写已推送历史。
- **禁止** `git add .` / `git add -A`；只 stage 与本次任务相关的路径。
- **不要**提交明显含密钥的文件（`.env`、credentials 等）；若用户坚持，先警告。
- 本仓库 **Windows + PowerShell**：不用 Bash/WSL 写法；路径用 `E:\...`；串联用 `;`。
- 改完代码后 **不要**为验证而跑 build/compile（与用户规则一致）。

## 1. 摸清现状（并行）

在仓库根目录并行执行（只读）：

```powershell
git status
git branch -vv
git log -5 --oneline
git diff
git diff --staged
```

若涉及与远端同步，再执行：

```powershell
git fetch
git status -sb
```

记录：当前分支、是否跟踪远端、领先/落后提交数、是否有未合并路径、是否有冲突标记。

## 2. 意图路由

| 用户意图 | 动作 |
|----------|------|
| 点名本技能但未限定子任务（含 `/git-commit-push`、按本技能提交等） | **§3 Commit → §5 Push**（推送前按需 §4） |
| 只要提交（明确说不要 push） | §3 Commit only |
| 提交并推送 | §3 → §5 Push（推送前按需 §4） |
| 只要 push（已有本地提交） | §5 Push |
| pull / 拉取 / 更新本地 | §4 Pull |
| merge / 合并某分支 | §4 Merge |
| sync / 同步 / 和远端一致 | §4 Sync |
| 先同步再提交再推送 | §4 → §3 → §5 |

**默认分支名**：用 `git symbolic-ref refs/remotes/origin/HEAD` 或 `main`/`master` 中仓库实际存在者；不确定时向用户确认。

## 3. Commit

### 3.1 范围

- 只 `git add` 与本次变更相关的文件（可多次 `git add <path>`）。
- 提交前再次 `git diff --staged`，确认无多余文件、无密钥。

### 3.2 提交说明

- 读 `git log -10 --oneline` 对齐本仓库用语风格。
- 消息 1–2 句，说清 **为什么**，类型准确（feat / fix / refactor / docs / chore 等）。
- PowerShell 多行提交信息示例：

```powershell
$msg = @'
fix(auth): 修复权限缓存未随角色变更失效

角色变更后立即使 TTL 缓存失效，避免旧权限残留。
'@
git add path\to\file1 path\to\file2
git commit -m $msg
```

### 3.3 安全与 amend

- **仅**在用户明确要求且满足：HEAD 为本会话创建、未 push、或 hook 改文件需重提时，才考虑 `git commit --amend`。
- **Hook 失败**：修问题后 **新 commit**，不要 amend 失败的那次。
- **已 push 到远端**：不要 amend（除非用户明确要求并接受 force-push 后果）。

### 3.4 提交后

```powershell
git status
```

- 若本次任务包含 push（启用本技能且用户未说「不 push」）：**不要在此停步**，继续 §4（按需）与 §5。

## 4. Pull / Merge / Sync

### 4.1 推送前是否需要先同步

若 `git status -sb` 显示当前分支 **behind** 远端，或用户要求 push/sync，或即将执行 §5：

1. 先 `git fetch`
2. 优先 **merge**（默认、冲突面可预期）：

```powershell
git pull origin <当前分支名>
```

用户明确要求 rebase 时：

```powershell
git pull --rebase origin <当前分支名>
```

### 4.2 合并其他分支（merge）

```powershell
git fetch
git merge <源分支>   # 或 git merge origin/<源分支>
```

合并前：工作区应干净（有未提交改动则先 commit/stash，并告知用户）。

### 4.3 Sync（与 IDE「同步」同类）

典型顺序：

1. `git fetch`
2. 若 behind：`git pull`（或用户指定的 rebase）
3. 若有本地提交且 ahead：`git push`
4. 若 **diverged**（既 ahead 又 behind）：先 pull（merge/rebase 按用户偏好），解决冲突后再 push；**不要**强推。

### 4.4 冲突

- 列出冲突文件，**不要**猜测业务逻辑；读冲突标记，结合用户意图或让其选择保留哪侧。
- 解决后：`git add <已解决文件>`，merge 用 `git commit`，rebase 用 `git rebase --continue`。
- 无法安全解决时：说明状态，给出 `git merge --abort` / `git rebase --abort` 选项，**不要**擅自 abort 除非用户同意。

## 5. Push（启用本技能后的必做步骤）

- **启用本技能且用户未明确「只 commit / 不 push」时**：§3 成功后**必须**执行 push，不得省略或改为口头让用户再说一声。
- **仅**在未启用本技能、且用户单次对话里只要求 push、或已明确不要推送时，才适用「未要求则不 push」。
- 首次推送当前分支：

```powershell
git push -u origin HEAD
```

- 已设上游：`git push`
- push 被拒（non-fast-forward）：回到 §4 先 pull/merge，再 push；**禁止**对共享主分支 force push。
- push 失败（网络、权限、保护分支等）：说明错误与已完成的 commit，给出后续操作建议，**不要**假装已成功推送。

## 6. 与仓库其它技能的关系

- **拆 PR / 多提交切片**：用户要拆分时用 `split-to-prs`，本技能不代替其规划步骤。
- **开 GitHub PR**：用户要 PR 时用 `creating-pull-requests`（`gh pr create`），本技能只负责本地 git 与 push。
- **含中文 frontend 源码**：提交前若改过 `frontend/**/*.{vue,ts,tsx}`，遵守 `.cursor/rules/frontend-utf8-editing.mdc`（Node UTF-8 补丁、无 `????`）。
- **与全局 user rule 的关系**：仓库默认「不主动 push」适用于**未**点名本技能的场景；用户点名 `git-commit-push` 即是对 push 的明确授权，优先遵循本技能。

## 7. 回报用户

结束时简短说明：

- 分支名、commit hash（若有）、**是否已执行 push**（成功 / 失败原因）
- 与远端关系（up to date / ahead N / behind N）
- 未提交的剩余改动或冲突待办

**禁止**在启用本技能且已完成 commit 时，以「若要推到远端可以说一声」作为结束语。

## 示例（显式启用）

**用户**：`/git-commit-push` 把权限缓存改动提交并推到 origin`

1. 并行 status / diff / log / branch -vv  
2. `git add` 相关 py/ts 文件  
3. `$msg = @'...'@` → `git commit`  
4. `git fetch` → 若 behind 则 `git pull` → **`git push -u origin HEAD`（必做）**  
5. 回报 hash、push 结果与同步状态

**用户**：`/git-commit-push`（无其它说明）

1. 同上，默认 **commit + push**，不要只 commit 后结束。

**用户**：`用 git-commit-push 技能先 pull main 再合并到我当前分支`

1. 确认当前分支与工作区干净  
2. `git fetch` → `git merge origin/main`（或用户指定的 main）  
3. 有冲突则列出文件并协助解决，不自动 force

**用户**：`按 git-commit-push 只提交，先别推`

1. §3 Commit → 回报说明**未推送**（此为用户声明的例外）
