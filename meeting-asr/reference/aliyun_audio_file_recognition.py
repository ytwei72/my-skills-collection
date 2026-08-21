#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云NLS录音文件识别工具，适配移动云EOS S3存储
功能：
    1. 将本地音频上传至S3(EOS)对象存储
    2. 生成公网预签名下载URL
    3. 调用阿里云录音文件识别接口
    4. 轮询获取识别结果，原始JSON结果输出至指定目录

依赖安装：
    pip install boto3 aliyun-python-sdk-core

命令行使用方式：
    # 方式1：必传音频路径，输出到【当前工作目录】
    python aliyun_audio_file_recognition.py ./高通进军AI基建与定制芯片.m4a

    # 方式2：指定输出结果存放目录（目录不存在会自动创建）
    python aliyun_audio_file_recognition.py /data/audio/高通进军AI基建与定制芯片.m4a /data/asr_output

参数说明：
    audio_path   【必传】音频文件，支持相对路径/绝对路径；支持格式：wav / mp3 / m4a，最大500MB
    output_dir   【可选】识别结果json输出目录，不填默认当前目录

配置修改：
    需要修改脚本【配置区】下面的变量：
        S3_ACCESS_KEY / S3_SECRET_KEY / S3_ENDPOINT / S3_BUCKET  移动云EOS信息
        ALIYUN_ACCESS_KEY_ID / ALIYUN_ACCESS_KEY_SECRET         阿里云账号AccessKey
        ALIYUN_NLS_APPKEY                                       智能语音交互项目AppKey

输出产物：
    成功： nls_raw_result_<taskId>.json  阿里云完整原始返回
    失败： nls_failed_<taskId>.json       失败原始响应
脚本控制台最后输出简短任务信息JSON。
"""
# # ==========自动安装依赖==========
# import importlib.util
# import subprocess
# import sys
#
# def install_if_missing(package: str):
#     if not importlib.util.find_spec(package):
#         print(f"未检测到依赖 {package}，尝试自动pip安装……")
#         subprocess.check_call([sys.executable, "-m", "pip", "install", package])
#
# install_if_missing("boto3")
# install_if_missing("aliyun-python-sdk-core")

import json
import os
import time
import argparse
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urlunparse

import boto3
from aliyunsdkcore.acs_exception.exceptions import ClientException, ServerException
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from boto3.s3.transfer import TransferConfig
from botocore import config
from botocore.exceptions import ClientError

# ====================== 配置区======================
# S3配置
S3_ACCESS_KEY = "YOUR_EOS_ACCESS_KEY"
S3_SECRET_KEY = "YOUR_EOS_SECRET_KEY"
S3_ENDPOINT = "http://eos-wuxi-5.cmecloud.cn"
S3_BUCKET = "aibs"
S3_PREFIX = "asr/audio_files/"  # s3里面存放音频的目录前缀
# 如果需要替换预签名返回的域名，填写公网域名；不需要替换就填 None
S3_PRESIGNED_ENDPOINT_URL: Optional[str] = None
# 阿里离线识别最大500MB，设置分片阈值500MB，小于该文件直接单文件上传，不走分片
S3_TRANSFER_CONFIG = TransferConfig(
    multipart_threshold=500 * 1024 * 1024,  # 500MB才启用分片
    multipart_chunksize=100 * 1024 * 1024,
)

# 阿里云配置 智能语音交互项目的AppKey
ALIYUN_NLS_APP_KEY = "YOUR_NLS_APP_KEY"
ALIYUN_ACCESS_KEY_ID = "YOUR_ALIYUN_ACCESS_KEY_ID"
ALIYUN_ACCESS_KEY_SECRET = "YOUR_ALIYUN_ACCESS_KEY_SECRET"

# 阿里离线识别模型，通用中文
REGION_ID = "cn-shanghai"
PRODUCT = "nls-filetrans"
DOMAIN = "filetrans.cn-shanghai.aliyuncs.com"
API_VERSION = "2018-08-17"
ACTION_SUBMIT = "SubmitTask"
ACTION_QUERY = "GetTaskResult"

# 轮询配置
POLL_INTERVAL = 20  # 每20秒查一次任务状态
MAX_WAIT_SECONDS = 60 * 30  # 最大等待30分钟，超时退出
PRESIGNED_EXPIRE_SEC = 60 * 60 * 6  # 签名有效期6小时


# =================================================================


# ====================== 配置区======================


# =================================================================


def build_presigned_url(
        object_key: str,
        bucket: str,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        expires_in: int,
        presigned_endpoint_override: Optional[str] = None
) -> Optional[str]:
    """
    生成 get_object 的预签名下载URL
    :param object_key: s3对象key
    :param bucket: bucket名称
    :param endpoint_url: s3服务endpoint
    :param access_key: s3 ak
    :param secret_key: s3 sk
    :param expires_in: 签名过期秒
    :param presigned_endpoint_override: 覆盖输出url的域名，None则不替换
    :return: http预签名url，失败返回None
    """
    params = {
        "Bucket": bucket,
        "Key": object_key
    }
    s3_cfg = config.Config(s3={"addressing_style": "path"})
    client = boto3.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        endpoint_url=endpoint_url,
        config=s3_cfg
    )
    t0 = time.monotonic()
    try:
        url = client.generate_presigned_url(
            ClientMethod="get_object",
            Params=params,
            ExpiresIn=expires_in
        )
        if url and presigned_endpoint_override:
            parsed_url = urlparse(url)
            base_parse = urlparse(presigned_endpoint_override)
            url = urlunparse((
                base_parse.scheme,
                base_parse.netloc,
                parsed_url.path,
                parsed_url.params,
                parsed_url.query,
                parsed_url.fragment
            ))
        cost_ms = (time.monotonic() - t0) * 1000
        print(f"生成预签名url成功, cost={cost_ms:.1f}ms key={object_key}")
        return url
    except ClientError as e:
        cost_ms = (time.monotonic() - t0) * 1000
        print(f"生成预签名url失败 cost={cost_ms:.1f}ms, error={str(e)}")
        return None


def validate_audio_file(file_path: str) -> tuple[bool, str]:
    p = Path(file_path)
    if not p.exists():
        return False, f"文件不存在:{file_path}"
    if not p.is_file():
        return False, f"不是有效文件:{file_path}"

    file_size = os.path.getsize(file_path)
    max_size = 500 * 1024 * 1024
    if file_size > max_size:
        return False, f"文件超过500MB限制，size={file_size}"

    allow_suffix = {".wav", ".mp3", ".m4a"}
    suffix = p.suffix.lower()
    if suffix not in allow_suffix:
        return False, f"不支持文件后缀 {suffix}，允许{allow_suffix}"

    return True, "ok"


def upload_file_to_s3(local_file_path: str) -> str:
    """上传本地文件，返回 object_key"""
    p = Path(local_file_path)
    s3_key = f"{S3_PREFIX}{p.name}"
    s3_config = config.Config(s3={"addressing_style": "path"})
    s3 = boto3.client(
        "s3",
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        endpoint_url=S3_ENDPOINT,
        config=s3_config
    )
    # ✅传入 transfer_config，避免自动分片
    s3.upload_file(
        Filename=local_file_path,
        Bucket=S3_BUCKET,
        Key=s3_key,
        Config=S3_TRANSFER_CONFIG
    )
    return s3_key


def submit_ali_asr_task(client: AcsClient, audio_http_presigned_url: str) -> str:
    task_body = {
        "appkey": ALIYUN_NLS_APP_KEY,
        "file_link": audio_http_presigned_url,
        "auto_split": True,
        "version": "4.0",
        "supervise_type": 1,
        "speaker_num": 6,
        "enable_words": False,
        "enable_sample_rate_adaptive": True,
    }
    print("===提交NLS任务，task_body===")
    print(json.dumps(task_body, ensure_ascii=False, indent=2))

    post_req = CommonRequest()
    post_req.set_domain(DOMAIN)
    post_req.set_version(API_VERSION)
    post_req.set_product(PRODUCT)
    post_req.set_action_name(ACTION_SUBMIT)
    post_req.set_method("POST")
    post_req.add_body_params("Task", json.dumps(task_body))

    try:
        raw_resp = client.do_action_with_exception(post_req)
    except ServerException as e:
        # 打印关键排错信息
        print(f"!!!ServerException!!!")
        print(f"request_id: {e.request_id}")
        print(f"error_code: {e.error_code}")
        print(f"message: {e.message}")
        raise
    except ClientException as e:
        print(f"!!!ClientException!!!")
        print(f"error_code: {e.error_code}")
        print(f"message: {e.message}")
        raise

    resp_data = json.loads(raw_resp)
    status_text = resp_data.get("StatusText", "")
    if status_text != "SUCCESS":
        raise RuntimeError(f"NLS任务提交失败，StatusText:{status_text}, resp:{resp_data}")

    task_id = resp_data.get("TaskId", "")
    if not task_id:
        raise RuntimeError("提交任务返回taskId为空")
    return task_id

def poll_ali_task_result(client: AcsClient, task_id: str, output_dir: Path) -> dict:
    start_time = time.time()
    while True:
        if time.time() - start_time > MAX_WAIT_SECONDS:
            raise TimeoutError(f"任务轮询超时，taskId={task_id}")

        get_req = CommonRequest()
        get_req.set_domain(DOMAIN)
        get_req.set_version(API_VERSION)
        get_req.set_product(PRODUCT)
        get_req.set_action_name(ACTION_QUERY)
        get_req.set_method("GET")
        get_req.add_query_param("TaskId", task_id)

        raw_resp = client.do_action_with_exception(get_req)
        resp_data = json.loads(raw_resp)
        status_text = resp_data.get("StatusText", "")

        if status_text == "SUCCESS":
            out_file = output_dir / f"nls_raw_result_{task_id}.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(resp_data, f, ensure_ascii=False, indent=2)
            print(f"原始识别结果已写入: {str(out_file)}")
            return resp_data
            # return

        if status_text == "FAILED":
            err_file = output_dir / f"nls_failed_{task_id}.json"
            with open(err_file, "w", encoding="utf-8") as f:
                json.dump(resp_data, f, ensure_ascii=False, indent=2)
            raise RuntimeError(f"识别任务失败，详情写入 {str(err_file)}")

        print(f"task {task_id} 当前状态：{status_text}，等待中...")
        time.sleep(POLL_INTERVAL)


def main(audio_local_path: str, output_dir: Path):
    ok, msg = validate_audio_file(audio_local_path)
    if not ok:
        print(f"文件不存在:{audio_local_path}")

    try:
        print(f"准备将文件上传至s3：{audio_local_path}")
        object_key = upload_file_to_s3(audio_local_path)
        print(f"已经将文件上传至s3,开时生成预签名：{object_key}")
        # 生成预签名下载url
        presigned_url = build_presigned_url(
            object_key=object_key,
            bucket=S3_BUCKET,
            endpoint_url=S3_ENDPOINT,
            access_key=S3_ACCESS_KEY,
            secret_key=S3_SECRET_KEY,
            expires_in=PRESIGNED_EXPIRE_SEC,
            presigned_endpoint_override=S3_PRESIGNED_ENDPOINT_URL
        )

        print(f"生成预签名：{presigned_url}")
        if not presigned_url:
            raise RuntimeError("生成S3预签名URL返回为空")

        print("开始连接阿里云")
        client = AcsClient(ALIYUN_ACCESS_KEY_ID, ALIYUN_ACCESS_KEY_SECRET, REGION_ID)
        # print(f"已创建阿里连接，准备提交待识别音频，{presigned_url}")
        task_id = submit_ali_asr_task(client, presigned_url)
        # task_id = "d7234b8c437949e79e2e6c29f76ec294"
        print(f"异步识别任务的任务id为:{task_id}")
        poll_ali_task_result(client, task_id, output_dir)
        # return result
    except Exception as e:
        print("任务执行失败，", e)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="阿里云老版NLS录音文件识别脚本")
    parser.add_argument("audio_path", help="待识别音频，相对路径或绝对路径(wav/mp3/m4a)")
    parser.add_argument("output_dir", nargs="?", default=None, help="[可选]输出结果目录，默认当前目录")
    args = parser.parse_args()

    audio_path = args.audio_path
    if args.output_dir is not None:
        out_dir = Path(args.output_dir)
    else:
        out_dir = Path.cwd()

    # 目录不存在自动创建
    out_dir.mkdir(parents=True, exist_ok=True)

    main(audio_path, out_dir)