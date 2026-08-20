# meeting-asr

把**会议发言录音**转成带说话人、时间戳的文字稿（Markdown）。底层是：本地文件上传到移动云 EOS → 阿里云录音文件识别（NLS）。

> **说明**：本文件供**人类**查阅。Agent 仅在用户**明确点名**本 skill 时加载 `SKILL.md`。

---

## 如何触发

本 skill 须**点名**才会加载，例如：

- `/meeting-asr`
- `@meeting-asr`
- 「用 meeting-asr 技能…」
- 「按 meeting-asr 把会议录音转写成文字」

未点名时 Agent 不会自动启用本技能。

---

## 首次配置

在 `scripts/` 下复制一份配置（该文件已加入 gitignore，不要提交）：

```powershell
copy .cursor\skills\meeting-asr\scripts\config.example.json .cursor\skills\meeting-asr\scripts\config.json
```

打开 `config.json`，填入：

- 移动云 EOS：`access_key` / `secret_key` / `endpoint` / `bucket`
- 阿里云智能语音：`access_key_id` / `access_key_secret` / `nls_app_key`

若本机已有 `E:\Develop\DocsRep\toolkits\asr\aliyun_audio_file_recognition.py`，可把该脚本配置区里的同名变量抄过来。

也可改用环境变量 `MEETING_ASR_CONFIG` 指向任意 JSON 路径。

依赖（推荐用 uv）：

```powershell
uv pip install -r .cursor\skills\meeting-asr\scripts\requirements.txt
```

当前项目由 uv 管理时，也可写入项目依赖：

```powershell
uv add -r .cursor\skills\meeting-asr\scripts\requirements.txt
```

---

## 自然语言命令示例

### 转写一段会议录音

```
用 meeting-asr 把 D:\recordings\周会.m4a 转成文字
```

```
/meeting-asr 转写这份会议录音：E:\会议\产品评审.mp3
```

### 指定说话人

```
用 meeting-asr 转写 周会.m4a，说话人按顺序是张三、李四、王五
```

```
大约 4 个人开会，用 meeting-asr 转写这段录音并按 4 人分离
```

### 只要重新排版（已经有识别 JSON）

```
用 meeting-asr 把 周会.nls.json 重新排成文稿，说话人改成 张三,李四
```

### 转写后再整理

```
用 meeting-asr 转写这段录音，再根据文稿写一份会议纪要
```

```
转写完成后把 Markdown 写成 Word
```

---

## 你会得到什么

与录音同目录（除非你指定输出目录）：

- `{文件名}.nls.json` — 识别服务的原始结果
- `{文件名}.transcript.md` — 按说话人合并的发言记录，带时间戳

说话人是算法分离的标签（说话人1、说话人2…），不是通讯录姓名；你可以用「说话人按顺序是…」让 Agent 重新映射。

识别是离线任务，几分钟到几十分钟都正常。免费额度与并发以阿里云账号为准。

---

## 说法提示

| 你想做的事 | 可以这样说 |
|-----------|-----------|
| 默认转写 | 「用 meeting-asr 把这段会议录音转成文字」 |
| 指定姓名 | 「说话人是张三、李四」 |
| 指定人数 | 「按 4 个人分离说话人」 |
| 只要纪要 | 「转写完再写成会议纪要」 |
| 已有 JSON | 「用这份 .nls.json 重新排版」 |
| 指定输出目录 | 「结果放到 D:\asr_out」 |

---

## 与其他 skill 的边界

| 需求 | 说明 |
|------|------|
| 会议录音 → 逐字稿 | 用本 skill |
| 逐字稿 → 飞书文档 | 转写后用 `feishu-doc-writer` |
| 逐字稿 → Word / HTML | 转写后用 `md-to-word` / `md-to-rich-html` |
| 实时对着麦克风说 | 不用本 skill |

Agent 执行细节见 [SKILL.md](SKILL.md)。

---

## 在新项目中挂载本 Skill（目录 Junction）

本 skill 放在共享库 `my-skills-collection` 里，不必拷贝进业务项目。在目标项目的 `.cursor/skills/` 下建一个指向本目录的 **Junction**（Windows 目录联接）即可；`git pull` 共享库后，各项目自动用到最新内容。

推荐在 Cursor 里用自然语言让 Agent 创建链接（把路径换成你本机实际路径）。

### 推荐说法（复制后改路径）

```
在当前项目的 .cursor/skills 目录下，用目录 Junction 挂载共享 skill：
链接名 meeting-asr，目标指向
E:\Develop\AI-Agents\my-skills-collection\meeting-asr。
若 .cursor\skills 不存在就先创建；若已有同名真实目录先别删，告诉我；
若已有指向别处的 Junction 则先删再建。不要把 Junction 提交进 Git。
```

一次挂多个 skill 时可以说：

```
把 E:\Develop\AI-Agents\my-skills-collection 里的这些 skill
用 Junction 链到本项目 .cursor\skills\ 下（同名目录）：
meeting-asr、md-to-word、feishu-doc-writer。
路径按本机实际位置调整；已存在且指向正确的跳过；
不要提交这些链接。
```

### 等价的 PowerShell（自己执行时）

```powershell
$skillsDir = "D:\path\to\YourProject\.cursor\skills"
$libSkill  = "E:\Develop\AI-Agents\my-skills-collection\meeting-asr"
New-Item -ItemType Directory -Force -Path $skillsDir | Out-Null
New-Item -ItemType Junction -Path (Join-Path $skillsDir "meeting-asr") -Target $libSkill
```

### 注意

- Junction 目标必须是本机上的绝对路径；换电脑时在那台机器上再挂一次即可。
- 业务项目 `.gitignore` 应忽略这些链接目录，避免把共享 skill 误提交进项目仓库。
- `scripts/config.json` 含密钥，只放本机，不要提交。
