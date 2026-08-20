#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""会议录音转写：本地音频 → 移动云 EOS → 阿里云 NLS 录音文件识别 → 带说话人的文稿。"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse, urlunparse

AUDIO_SUFFIXES = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".amr", ".wma"}
VIDEO_SUFFIXES = {".mp4"}
ALLOW_SUFFIXES = AUDIO_SUFFIXES | VIDEO_SUFFIXES
AUDIO_MAX_BYTES = 512 * 1024 * 1024
VIDEO_MAX_BYTES = 2 * 1024 * 1024 * 1024
CONTENT_TYPES = {
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".aac": "audio/aac",
    ".flac": "audio/flac",
    ".ogg": "audio/ogg",
    ".amr": "audio/amr",
    ".wma": "audio/x-ms-wma",
    ".mp4": "video/mp4",
}
POLL_OK = "SUCCESS"
POLL_WAIT = {"QUEUEING", "RUNNING"}
REGION_DOMAIN = {
    "cn-shanghai": "filetrans.cn-shanghai.aliyuncs.com",
    "cn-beijing": "filetrans.cn-beijing.aliyuncs.com",
    "cn-shenzhen": "filetrans.cn-shenzhen.aliyuncs.com",
}


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def emit(payload: dict[str, Any], code: int) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(code)


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def load_json_file(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8-sig")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise RuntimeError(f"配置不是 JSON 对象: {path}")
    return data


def merge_dict(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for k, v in overlay.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge_dict(out[k], v)
        elif v is not None:
            out[k] = v
    return out


def config_search_paths() -> list[Path]:
    paths: list[Path] = []
    env_path = os.environ.get("MEETING_ASR_CONFIG")
    if env_path:
        paths.append(Path(env_path).expanduser())
    paths.append(script_dir() / "config.json")
    paths.append(Path.home() / ".meeting-asr" / "config.json")
    return paths


def load_config_file() -> dict[str, Any]:
    for path in config_search_paths():
        if path.is_file():
            log(f"读取配置: {path}")
            return load_json_file(path)
    example = script_dir() / "config.example.json"
    raise RuntimeError(
        "未找到配置文件。请复制 "
        f"{example} 为 scripts/config.json 并填入密钥；"
        "或设置环境变量 MEETING_ASR_CONFIG 指向配置 JSON。"
    )


def env_overlay() -> dict[str, Any]:
    s3 = {
        "access_key": os.environ.get("MEETING_ASR_S3_ACCESS_KEY"),
        "secret_key": os.environ.get("MEETING_ASR_S3_SECRET_KEY"),
        "endpoint": os.environ.get("MEETING_ASR_S3_ENDPOINT"),
        "bucket": os.environ.get("MEETING_ASR_S3_BUCKET"),
        "prefix": os.environ.get("MEETING_ASR_S3_PREFIX"),
        "presigned_endpoint_url": os.environ.get("MEETING_ASR_S3_PRESIGNED_ENDPOINT"),
    }
    aliyun = {
        "access_key_id": os.environ.get("ALIYUN_ACCESS_KEY_ID")
        or os.environ.get("MEETING_ASR_ALIYUN_ACCESS_KEY_ID"),
        "access_key_secret": os.environ.get("ALIYUN_ACCESS_KEY_SECRET")
        or os.environ.get("MEETING_ASR_ALIYUN_ACCESS_KEY_SECRET"),
        "nls_app_key": os.environ.get("ALIYUN_NLS_APPKEY")
        or os.environ.get("MEETING_ASR_NLS_APP_KEY"),
        "region_id": os.environ.get("MEETING_ASR_ALIYUN_REGION"),
    }
    return {
        "s3": {k: v for k, v in s3.items() if v},
        "aliyun": {k: v for k, v in aliyun.items() if v},
    }


def require_config() -> dict[str, Any]:
    cfg = merge_dict(load_config_file(), env_overlay())
    s3 = cfg.get("s3") or {}
    ali = cfg.get("aliyun") or {}
    missing = []
    for key in ("access_key", "secret_key", "endpoint", "bucket"):
        if not s3.get(key):
            missing.append(f"s3.{key}")
    for key in ("access_key_id", "access_key_secret", "nls_app_key"):
        if not ali.get(key):
            missing.append(f"aliyun.{key}")
    if missing:
        raise RuntimeError("配置缺少: " + ", ".join(missing))
    s3.setdefault("prefix", "asr/audio_files/")
    ali.setdefault("region_id", "cn-shanghai")
    cfg["s3"] = s3
    cfg["aliyun"] = ali
    return cfg


def validate_audio(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    if not path.is_file():
        raise ValueError(f"不是有效文件: {path}")
    suffix = path.suffix.lower()
    if suffix not in ALLOW_SUFFIXES:
        raise ValueError(f"不支持后缀 {suffix}，允许 {sorted(ALLOW_SUFFIXES)}")
    size = path.stat().st_size
    limit = VIDEO_MAX_BYTES if suffix in VIDEO_SUFFIXES else AUDIO_MAX_BYTES
    if size > limit:
        raise ValueError(f"文件过大 size={size}，上限 {limit} 字节")


def safe_object_name(path: Path) -> str:
    ts = time.strftime("%Y%m%d_%H%M%S")
    stem = path.stem
    suffix = path.suffix.lower() or ".bin"
    if stem.isascii() and re.fullmatch(r"[A-Za-z0-9._-]+", stem):
        return f"{ts}_{stem}{suffix}"
    return f"{ts}_{uuid.uuid4().hex[:10]}{suffix}"


def s3_client(s3_cfg: dict[str, Any]):
    import boto3
    from botocore import config as botocore_config

    return boto3.client(
        "s3",
        aws_access_key_id=s3_cfg["access_key"],
        aws_secret_access_key=s3_cfg["secret_key"],
        endpoint_url=s3_cfg["endpoint"],
        config=botocore_config.Config(s3={"addressing_style": "path"}),
    )


def upload_and_presign(local_path: Path, s3_cfg: dict[str, Any], expires_in: int) -> tuple[str, str]:
    from boto3.s3.transfer import TransferConfig

    prefix = str(s3_cfg.get("prefix") or "asr/audio_files/").strip("/")
    key = f"{prefix}/{safe_object_name(local_path)}"
    extra = {}
    ctype = CONTENT_TYPES.get(local_path.suffix.lower())
    if ctype:
        extra["ContentType"] = ctype
    transfer = TransferConfig(
        multipart_threshold=500 * 1024 * 1024,
        multipart_chunksize=100 * 1024 * 1024,
    )
    client = s3_client(s3_cfg)
    log(f"上传到 EOS: s3://{s3_cfg['bucket']}/{key}")
    upload_kwargs = {
        "Filename": str(local_path),
        "Bucket": s3_cfg["bucket"],
        "Key": key,
        "Config": transfer,
    }
    if extra:
        upload_kwargs["ExtraArgs"] = extra
    client.upload_file(**upload_kwargs)
    url = client.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": s3_cfg["bucket"], "Key": key},
        ExpiresIn=expires_in,
    )
    override = s3_cfg.get("presigned_endpoint_url")
    if url and override:
        parsed = urlparse(url)
        base = urlparse(override)
        url = urlunparse(
            (base.scheme, base.netloc, parsed.path, parsed.params, parsed.query, parsed.fragment)
        )
    if not url:
        raise RuntimeError("生成预签名 URL 失败")
    log("预签名 URL 已生成")
    return key, url


def nls_client(ali_cfg: dict[str, Any]):
    from aliyunsdkcore.client import AcsClient

    return AcsClient(ali_cfg["access_key_id"], ali_cfg["access_key_secret"], ali_cfg["region_id"])


def build_task_body(appkey: str, file_link: str, args: argparse.Namespace) -> dict[str, Any]:
    body: dict[str, Any] = {
        "appkey": appkey,
        "file_link": file_link,
        "version": "4.0",
        "enable_words": False,
        "enable_sample_rate_adaptive": True,
        "enable_punctuation_prediction": True,
        "enable_inverse_text_normalization": True,
        "enable_disfluency": not args.keep_fillers,
    }
    if args.speaker_num == 1:
        body["auto_split"] = False
        return body
    body["auto_split"] = True
    if args.supervise == "auto":
        body["supervise_type"] = 2
    else:
        body["supervise_type"] = 1
        body["speaker_num"] = args.speaker_num
    return body


def submit_task(client: Any, domain: str, task_body: dict[str, Any]) -> str:
    from aliyunsdkcore.acs_exception.exceptions import ClientException, ServerException
    from aliyunsdkcore.request import CommonRequest

    log("提交 NLS 任务:\n" + json.dumps(task_body, ensure_ascii=False, indent=2))
    req = CommonRequest()
    req.set_domain(domain)
    req.set_version("2018-08-17")
    req.set_product("nls-filetrans")
    req.set_action_name("SubmitTask")
    req.set_method("POST")
    req.add_body_params("Task", json.dumps(task_body, ensure_ascii=False))
    try:
        raw = client.do_action_with_exception(req)
    except ServerException as e:
        raise RuntimeError(f"SubmitTask ServerException code={e.error_code} msg={e.message}") from e
    except ClientException as e:
        raise RuntimeError(f"SubmitTask ClientException code={e.error_code} msg={e.message}") from e
    data = json.loads(raw)
    if data.get("StatusText") != POLL_OK:
        raise RuntimeError(f"任务提交失败: {data}")
    task_id = data.get("TaskId") or ""
    if not task_id:
        raise RuntimeError(f"提交成功但 TaskId 为空: {data}")
    log(f"任务已提交 TaskId={task_id}")
    return task_id


def poll_task(client: Any, domain: str, task_id: str, poll_interval: int, max_wait: int) -> dict[str, Any]:
    from aliyunsdkcore.request import CommonRequest

    start = time.time()
    while True:
        elapsed = time.time() - start
        if elapsed > max_wait:
            raise TimeoutError(f"轮询超时（{max_wait}s），TaskId={task_id}")
        req = CommonRequest()
        req.set_domain(domain)
        req.set_version("2018-08-17")
        req.set_product("nls-filetrans")
        req.set_action_name("GetTaskResult")
        req.set_method("GET")
        req.add_query_param("TaskId", task_id)
        data = json.loads(client.do_action_with_exception(req))
        status = data.get("StatusText") or ""
        if status == POLL_OK:
            log(f"识别完成 TaskId={task_id}")
            return data
        if status in POLL_WAIT:
            log(f"TaskId={task_id} 状态={status}，已等待 {int(elapsed)}s")
            time.sleep(poll_interval)
            continue
        raise RuntimeError(f"识别失败 StatusText={status} resp={data}")


def parse_result_object(resp: dict[str, Any]) -> dict[str, Any]:
    result = resp.get("Result")
    if isinstance(result, str):
        result = json.loads(result) if result else {}
    if result is None:
        return {}
    if not isinstance(result, dict):
        raise RuntimeError(f"无法解析 Result 字段: {type(result)}")
    return result


def speaker_key(sentence: dict[str, Any]) -> str:
    if "SpeakerId" in sentence and sentence["SpeakerId"] not in (None, ""):
        return str(sentence["SpeakerId"])
    if "ChannelId" in sentence and sentence["ChannelId"] not in (None, ""):
        return str(sentence["ChannelId"])
    return "0"


def join_text(left: str, right: str) -> str:
    if not left:
        return right
    if not right:
        return left
    if left[-1] in " \t\n。！？；，、,.!?;:" or right[0] in " \t\n。！？；，、,.!?;:":
        return left + right
    if any("\u4e00" <= ch <= "\u9fff" for ch in (left[-1] + right[0])):
        return left + right
    return left + " " + right


def fmt_ts(ms: int) -> str:
    ms = max(0, int(ms))
    total = ms // 1000
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def display_stem(audio_name: str) -> str:
    name = Path(audio_name).name
    if name.endswith(".nls.json"):
        return name[: -len(".nls.json")]
    return Path(name).stem


def fmt_duration(ms: int) -> str:
    ms = max(0, int(ms))
    total = ms // 1000
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}小时{m}分{s}秒"
    if m:
        return f"{m}分{s}秒"
    return f"{s}秒"


def build_speaker_names(keys: list[str], names: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    numeric = True
    values: list[int] = []
    for k in keys:
        if re.fullmatch(r"-?\d+", k):
            values.append(int(k))
        else:
            numeric = False
            break
    ordered = [str(v) for v in sorted(set(values))] if numeric else list(dict.fromkeys(keys))
    for i, key in enumerate(ordered):
        if i < len(names) and names[i]:
            mapping[key] = names[i]
        else:
            mapping[key] = f"说话人{i + 1}"
    return mapping


def merge_turns(sentences: list[dict[str, Any]]) -> list[dict[str, Any]]:
    turns: list[dict[str, Any]] = []
    for sent in sentences:
        text = (sent.get("Text") or "").strip()
        if not text:
            continue
        key = speaker_key(sent)
        begin = int(sent.get("BeginTime") or 0)
        end = int(sent.get("EndTime") or begin)
        if turns and turns[-1]["speaker_key"] == key:
            turns[-1]["text"] = join_text(turns[-1]["text"], text)
            turns[-1]["end"] = max(turns[-1]["end"], end)
            turns[-1]["count"] += 1
        else:
            turns.append(
                {
                    "speaker_key": key,
                    "begin": begin,
                    "end": end,
                    "text": text,
                    "count": 1,
                }
            )
    return turns


def render_markdown(
    *,
    audio_name: str,
    task_id: str,
    duration_ms: int,
    turns: list[dict[str, Any]],
    speaker_names: dict[str, str],
) -> str:
    used = list(dict.fromkeys(t["speaker_key"] for t in turns))
    speakers_line = "、".join(speaker_names.get(k, k) for k in used) or "（未能分离说话人）"
    lines = [
        f"# 会议转写：{display_stem(audio_name)}",
        "",
        "| 项目 | 内容 |",
        "|------|------|",
        f"| 音频 | {audio_name} |",
        f"| 任务 ID | {task_id or '—'} |",
        f"| 音频时长 | {fmt_duration(duration_ms)} |",
        f"| 说话人 | {speakers_line} |",
        f"| 发言段数 | {len(turns)} |",
        "",
        "> 说话人由算法分离，标签不一定等于真实姓名。可用 `--speakers 张三,李四` 映射。",
        "",
        "## 发言记录",
        "",
    ]
    if not turns:
        lines.append("（识别结果为空）")
        lines.append("")
        return "\n".join(lines)
    for turn in turns:
        name = speaker_names.get(turn["speaker_key"], f"说话人{turn['speaker_key']}")
        span = f"`{fmt_ts(turn['begin'])}`–`{fmt_ts(turn['end'])}`"
        lines.append(f"**{name}** · {span}")
        lines.append("")
        lines.append(turn["text"])
        lines.append("")
    return "\n".join(lines)


def parse_speaker_names(raw: Optional[str]) -> list[str]:
    if not raw:
        return []
    parts = [p.strip() for p in re.split(r"[,，]", raw)]
    return [p for p in parts if p]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def resolve_output_paths(audio_path: Optional[Path], output_dir: Path, from_json: Optional[Path]) -> tuple[Path, Path]:
    if audio_path is not None:
        stem = audio_path.stem
    elif from_json is not None:
        stem = from_json.stem.replace(".nls", "") or from_json.stem
    else:
        stem = "meeting"
    return output_dir / f"{stem}.nls.json", output_dir / f"{stem}.transcript.md"


def format_from_response(
    resp: dict[str, Any],
    audio_name: str,
    speaker_name_list: list[str],
) -> tuple[str, list[dict[str, Any]], dict[str, str], int]:
    result = parse_result_object(resp)
    sentences = result.get("Sentences") or []
    if not isinstance(sentences, list):
        sentences = []
    turns = merge_turns(sentences)
    keys = [t["speaker_key"] for t in turns]
    names = build_speaker_names(keys, speaker_name_list)
    duration_ms = int(resp.get("BizDuration") or 0)
    if duration_ms <= 0 and turns:
        duration_ms = max(t["end"] for t in turns)
    md = render_markdown(
        audio_name=audio_name,
        task_id=str(resp.get("TaskId") or ""),
        duration_ms=duration_ms,
        turns=turns,
        speaker_names=names,
    )
    return md, turns, names, duration_ms


def run_asr(audio_path: Path, cfg: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    validate_audio(audio_path)
    _key, url = upload_and_presign(audio_path, cfg["s3"], args.presign_expire)
    ali = cfg["aliyun"]
    region = ali["region_id"]
    domain = REGION_DOMAIN.get(region)
    if not domain:
        raise RuntimeError(f"不支持的 region_id: {region}，可选 {list(REGION_DOMAIN)}")
    client = nls_client(ali)
    body = build_task_body(ali["nls_app_key"], url, args)
    task_id = submit_task(client, domain, body)
    return poll_task(client, domain, task_id, args.poll_interval, args.max_wait)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="会议发言录音转写（阿里云 NLS + 移动云 EOS）")
    p.add_argument("audio_path", nargs="?", help="本地音频/视频路径（wav/mp3/m4a/mp4 等）")
    p.add_argument("-o", "--output-dir", default=None, help="输出目录，默认与音频同目录")
    p.add_argument("--from-json", default=None, help="已有 NLS 原始 JSON，只重新排版，不调用识别")
    p.add_argument("--speaker-num", type=int, default=6, help="说话人数（2-100）；与 --supervise named 联用")
    p.add_argument(
        "--supervise",
        choices=("auto", "named"),
        default="auto",
        help="auto=算法决定人数；named=使用 --speaker-num",
    )
    p.add_argument("--speakers", default=None, help="按发言先后映射姓名，逗号分隔，如 张三,李四")
    p.add_argument("--keep-fillers", action="store_true", help="保留「嗯/啊」等语气词")
    p.add_argument("--json-only", action="store_true", help="只写原始 JSON，不生成 Markdown")
    p.add_argument("--poll-interval", type=int, default=20, help="轮询间隔秒")
    p.add_argument("--max-wait", type=int, default=1800, help="最长等待秒，默认 30 分钟")
    p.add_argument("--presign-expire", type=int, default=6 * 3600, help="预签名 URL 有效期秒")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if args.speaker_num < 1 or args.speaker_num > 100:
        emit({"ok": False, "error": "--speaker-num 须在 1–100"}, 2)
    from_json = Path(args.from_json).expanduser() if args.from_json else None
    audio_path = Path(args.audio_path).expanduser() if args.audio_path else None
    if from_json is None and audio_path is None:
        emit({"ok": False, "error": "请提供 audio_path 或 --from-json"}, 2)
    if from_json is not None and not from_json.is_file():
        emit({"ok": False, "error": f"JSON 不存在: {from_json}"}, 2)

    if args.output_dir:
        output_dir = Path(args.output_dir).expanduser()
    elif audio_path is not None:
        output_dir = audio_path.parent
    elif from_json is not None:
        output_dir = from_json.parent
    else:
        output_dir = Path.cwd()
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path, md_path = resolve_output_paths(audio_path, output_dir, from_json)

    try:
        if from_json is not None:
            resp = load_json_file(from_json)
            raw_path = from_json
        else:
            assert audio_path is not None
            cfg = require_config()
            resp = run_asr(audio_path, cfg, args)
            write_json(raw_path, resp)

        audio_name = audio_path.name if audio_path is not None else str(resp.get("audio_name") or raw_path.name)
        md, turns, names, duration_ms = format_from_response(
            resp, audio_name, parse_speaker_names(args.speakers)
        )
        if not args.json_only:
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text(md, encoding="utf-8")
            log(f"转写文稿: {md_path}")
        emit(
            {
                "ok": True,
                "task_id": resp.get("TaskId"),
                "audio": str(audio_path) if audio_path else None,
                "raw_json": str(raw_path),
                "transcript_md": None if args.json_only else str(md_path),
                "duration_ms": duration_ms,
                "turn_count": len(turns),
                "speakers": names,
            },
            0,
        )
    except Exception as e:
        emit({"ok": False, "error": str(e)}, 1)


if __name__ == "__main__":
    main()
