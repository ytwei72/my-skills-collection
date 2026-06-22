---
name: feishu-doc-reader
disable-model-invocation: true
description: >-
  Use the local script toolkits\feishu\feishu_doc_reader.py to read Feishu documents.
  仅在用户明确点名本 skill（/feishu-doc-reader、使用 feishu-doc-reader 等）时加载。
  未点名时不要读取本技能；飞书链接读取可由 feishu-doc-auto 规则直接调用脚本。
---

# Feishu Doc Reader

## Trigger

Use this skill when either condition is true:

1. User intent includes reading/opening/parsing/summarizing a Feishu document.
2. Input contains Feishu document links in one unified pattern:
   - `https://*.feishu.cn/(docx|wiki|docs|sheets)/...`

## URL Recognition

Extract all matching URLs from user input. Use this regex pattern:

`https?://[^\s"'<>]+feishu\.cn/(?:docx|wiki|docs|sheets)/[A-Za-z0-9]+[^\s"'<>]*`

If multiple links are present, process them one by one in original order.

## Execution

Run the local reader script from repository root:

1. Preferred output format:
   - `.venv\Scripts\python.exe toolkits\feishu\feishu_doc_reader.py "<URL>" -f md`
2. Fallback if Markdown conversion fails:
   - `.venv\Scripts\python.exe toolkits\feishu\feishu_doc_reader.py "<URL>" -f text`
3. If still failing, return a clear error and include likely causes:
   - Missing `FEISHU_APP_ID` / `FEISHU_APP_SECRET`
   - App permission not granted
   - Document app not added as collaborator
