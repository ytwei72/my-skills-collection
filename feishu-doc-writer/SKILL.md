---
name: feishu-doc-writer
disable-model-invocation: true
description: >-
  Use the local script toolkits\feishu\feishu_doc_writer.py to write/overwrite a Feishu docx by path.
  仅在用户明确点名本 skill（/feishu-doc-writer、使用 feishu-doc-writer 等）时加载。
  未点名时不要读取本技能；飞书写入可由 feishu-doc-write-auto 规则直接调用脚本。
---

# Feishu Doc Writer

## Trigger

Use this skill when any condition is true:

1. User intent includes writing / updating / overwriting / creating / publishing / syncing content into a Feishu docx document.
2. Input contains a Feishu path literal in one of the two schemes:
   - `wiki://<space_name|my_library|space_id:xxx>/<dir>/.../<title>`
   - `drive://folder:<folder_token>/<dir>/.../<title>`

Note: writing always targets a **docx** document (not sheets/docs/bitable).

## Path Recognition

Extract the target path from user input using these patterns:

- Wiki: `wiki://[^\s"'<>]+`
- Drive: `drive://folder:[^\s"'<>]+`

If multiple paths are present, ask the user which one to use. If the path is ambiguous (e.g. a wiki space name that may not be unique), suggest switching to the explicit `space_id:<id>` form.

## Content Source

Decide the content to be written in this order:

1. Preferred — user provides a local file: pass it via `-i <FILE>`. Supported extensions: `.md` / `.markdown` / `.txt` / `.html` / `.htm` (will go through the official convert + descendant import flow).
2. User pastes multi-line text inline: first write it to a temporary file (e.g. `docs\_feishu_write_tmp.md`, UTF-8) and then use `-i`. Do NOT pass multi-line content via `-c`.
3. Only for short single-line text: `-c "<TEXT>"`.

## Execution

Run the local writer script from repository root (PowerShell):

1. Basic overwrite (intermediate directories must already exist):
   - `.venv\Scripts\python.exe toolkits\feishu\feishu_doc_writer.py "<PATH>" -i "<FILE>"`
2. Auto-create missing directories / leaf docx:
   - `.venv\Scripts\python.exe toolkits\feishu\feishu_doc_writer.py "<PATH>" -i "<FILE>" --create-parents`
3. Short inline text (single-line only):
   - `.venv\Scripts\python.exe toolkits\feishu\feishu_doc_writer.py "<PATH>" -c "<TEXT>"`

## Behavior & Safety

- The writer performs a **full overwrite** on the target docx: it clears all existing descendant blocks first, then writes the new content. Before running, briefly confirm with the user when the target looks like an important shared document.
- `--create-parents`:
  - For `wiki://` paths, auto-creates missing intermediate directories AND the leaf docx (both as `docx` wiki nodes).
  - For `drive://` paths, only auto-creates the leaf docx; intermediate folders must be pre-existing and shared to the app.
- `drive://` paths require an anchor folder that has been **explicitly shared to the app** (tenant_access_token cannot browse "My Space" root).

## Failure Diagnostics

If the script fails, return the stderr output and include likely causes:

- Missing `FEISHU_APP_ID` / `FEISHU_APP_SECRET` in `.env`.
- App lacks required scopes (docx read/write, wiki read/write, drive read/write, import_service).
- The knowledge space / drive folder has not been shared with the app.
- Wiki space name not found / not unique → suggest `space_id:<id>`.
- Drive intermediate directory missing → create it manually in Feishu first (drive mode does not auto-create intermediates).
- Leaf exists but is not a `docx` (e.g. `sheet` / `bitable`) → writer refuses to overwrite a non-docx leaf by design.
- `响应非 JSON: 404 page not found` → usually a transient gateway 404 on `/drive/v1/files` pagination, not a real "document missing". First verify whether the previous run already wrote the content by reading the target docx back with `feishu_doc_reader.py`; if content is already there, treat it as noise. Otherwise re-run the writer.
