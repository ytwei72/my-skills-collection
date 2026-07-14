---
name: pkg-disk-usage
disable-model-invocation: true
description: >-
  统计当前 Python 环境已安装依赖包的磁盘占用，按大小降序输出前 N 个包，可选导出 CSV。
  仅在用户明确点名时加载（/pkg-disk-usage、package disk usage、查看包体积、site-packages 占用等）。
  未点名时不要读取本技能。
---

# 已安装包磁盘占用统计

统计当前解释器环境中 `site-packages` 下各包体积，按大小降序展示，并汇总总占用。

## 何时启用

**仅**在用户**明确**要求使用本技能时执行，例如：

- `/pkg-disk-usage`
- 「用 pkg-disk-usage 技能…」
- 「统计已安装包体积 / 查看 site-packages 占用 / 哪些依赖最占磁盘」

## 脚本

路径：`.cursor/skills/pkg-disk-usage/scripts/pkg_disk_usage.py`

仅依赖标准库（`argparse` / `os` / `sys` / `importlib.metadata`），无第三方包。

优先用当前项目虚拟环境解释器：

```powershell
.venv\Scripts\python.exe .cursor\skills\pkg-disk-usage\scripts\pkg_disk_usage.py
.venv\Scripts\python.exe .cursor\skills\pkg-disk-usage\scripts\pkg_disk_usage.py --top 100
.venv\Scripts\python.exe .cursor\skills\pkg-disk-usage\scripts\pkg_disk_usage.py --csv package_sizes.csv
```

若无 `.venv`，用已激活的 `python` / `uv run`，只要目标环境与要统计的环境一致即可。

## 参数

| 参数 | 默认 | 说明 |
|------|------|------|
| `--top N` | `50` | 只打印前 N 个最大包 |
| `--csv PATH` | 无 | 将排名结果导出为 UTF-8-BOM CSV |

## 工作流

1. 确认用户要统计的环境（项目 `.venv` 优先；用户指定其他解释器则按其路径）。
2. 运行脚本；若报「未能定位到 site-packages」，说明未找到该环境的包目录，换解释器或先激活 venv 再重试。
3. 向用户汇报：表头排名结果、总包数与总占用；若写了 `--csv`，附上导出路径。

## 输出说明

- 按包名+版本去重；体积含 `dist-info`/`egg-info` 与 RECORD 中的已安装文件。
- 控制台列：排名、包名、版本、可读大小；CSV 另含字节数。
- 末行汇总：`共统计 N 个包，总占用: …`
