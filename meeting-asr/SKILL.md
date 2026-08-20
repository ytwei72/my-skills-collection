---
name: meeting-asr
description: >-
  将会议发言录音转写成带说话人分离和时间戳的文字稿。基于阿里云录音文件识别（NLS filetrans 4.0）
  与移动云 EOS 对象存储中转。仅在用户明确点名时加载（/meeting-asr、会议录音转写、发言录音转文字、
  会议逐字稿、ASR 转写、把 wav/mp3/m4a/mp4 会议录音转成文字等）。未点名时不要读取本技能。
disable-model-invocation: true
---

# 会议发言录音转写

把本地会议录音上传到移动云 EOS，生成公网预签名 URL，调用阿里云 NLS 录音文件识别，
再排版为带说话人、时间戳的 Markdown 文稿。

## 何时启用

**仅**在用户**明确**要求使用本技能时执行，例如：

- `/meeting-asr`
- 「用 meeting-asr 技能…」
- 「把这段会议录音转写成文字 / 逐字稿 / 发言记录」

不要用本技能做实时麦克风识别、翻译，或把转写结果直接当成已核对的会议纪要。

## 脚本

路径：`.cursor/skills/meeting-asr/scripts/transcribe.py`

依赖：`boto3`、`aliyun-python-sdk-core`（见同目录 `requirements.txt`）。

优先用当前项目虚拟环境解释器：

```powershell
.venv\Scripts\python.exe -m pip install -r .cursor\skills\meeting-asr\scripts\requirements.txt
.venv\Scripts\python.exe .cursor\skills\meeting-asr\scripts\transcribe.py "D:\recordings\周会.m4a"
```

无 `.venv` 时用已激活的 `python`。若命令找不到 `python`，改用本机安装路径下的 `python.exe`。识别可能要数分钟到半小时，Shell 的 `block_until_ms` 至少设 **1900000**（约 31 分钟）；更长音频把 `--max-wait` 和等待时间一并加大。

进度在 stderr，stdout 最后一行为任务摘要 JSON（`ok` / `transcript_md` / `raw_json`）。

## 配置

密钥**不要**写进对话或提交到 Git。读取顺序：

1. 环境变量 `MEETING_ASR_CONFIG` 指向的 JSON
2. `scripts/config.json`（已 gitignore）
3. `~/.meeting-asr/config.json`

环境变量可覆盖文件中的对应字段：`MEETING_ASR_S3_*`、`ALIYUN_ACCESS_KEY_ID`、`ALIYUN_ACCESS_KEY_SECRET`、`ALIYUN_NLS_APPKEY`。

首次使用若没有配置：

1. 复制 `scripts/config.example.json` 为 `scripts/config.json`
2. 若本机已有 `E:\Develop\DocsRep\toolkits\asr\aliyun_audio_file_recognition.py`，从其配置区填入 EOS / 阿里云字段
3. **不要**在回复中回显任何密钥

字段含义见 example：`s3`（EOS）+ `aliyun`（NLS AppKey 与 AccessKey）。

## 参数

| 参数 | 默认 | 说明 |
|------|------|------|
| `audio_path` | 必填* | 本地音频/视频。支持 wav / mp3 / m4a / aac / flac / ogg / amr / wma / mp4 |
| `-o` / `--output-dir` | 音频所在目录 | 输出目录，不存在则创建 |
| `--from-json PATH` | 无 | 已有 NLS 原始 JSON 时只重新排版，不调用识别 |
| `--supervise` | `auto` | `auto` 由算法决定说话人数；`named` 使用 `--speaker-num` |
| `--speaker-num N` | `6` | 仅 `--supervise named` 时生效；`1` 表示关闭说话人分离 |
| `--speakers` | 无 | 按发言先后映射姓名，逗号分隔，如 `张三,李四` |
| `--keep-fillers` | 关 | 保留「嗯/啊」等语气词 |
| `--json-only` | 关 | 只写原始 JSON |
| `--max-wait` | `1800` | 最长等待秒数 |

\* 使用 `--from-json` 时可不传音频。

音频上限 512MB，mp4 上限 2GB。对象存储 key 只用 ASCII，避免中文文件名导致阿里云下载失败。

## 工作流

1. 向用户确认音频路径；不存在则停止。用户给了说话人姓名或人数时带上 `--speakers` / `--supervise named --speaker-num`。
2. 确认 `scripts/config.json`（或环境变量）可用；缺失则按「配置」节补齐，**不要编造密钥**。
3. 缺依赖则先 `pip install -r scripts/requirements.txt`。
4. 运行 `transcribe.py`。轮询期间不要反复重提任务。
5. 读取 stdout 摘要。`ok=true` 时打开 `transcript_md`，把文稿路径和说话人列表告诉用户。
6. 失败时根据 `error` 处理：缺配置 → 补配置；文件格式/大小 → 请用户换文件；`FILE_DOWNLOAD_FAILED` → 检查 EOS 预签名与网络；超时 → 加大 `--max-wait` 后重试（同一文件会重新上传并新建任务）。

用户只要**逐字稿**：交 Markdown，不要擅自改写成纪要。  
用户明确要**会议纪要/摘要**：先完成转写，再基于文稿压缩（议题、结论、待办），并标明来自 ASR、可能有错字。

已有 `*.nls.json`、只需改说话人姓名时：

```powershell
python .cursor\skills\meeting-asr\scripts\transcribe.py --from-json "D:\recordings\周会.nls.json" --speakers 张三,李四,王五
```

## 产物

与音频同目录（或 `-o` 指定目录）：

- `{stem}.nls.json` — 阿里云原始返回
- `{stem}.transcript.md` — 按说话人合并后的发言记录

说话人标签来自 `SpeakerId` / `ChannelId`，先发言者通常编号较小，**不等于真实姓名**。

## 与其他 skill 的边界

| 需求 | 说明 |
|------|------|
| 录音 → 带说话人的文字稿 | 用本 skill |
| 把文稿写入飞书 | 转写完成后用 `feishu-doc-writer` |
| 文稿 → Word / HTML | 转写完成后用 `md-to-word` / `md-to-rich-html` |
| 实时麦克风识别 | 不用本 skill |
