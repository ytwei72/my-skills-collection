# -*- coding: utf-8 -*-
"""
统计当前 Python 环境中已安装依赖包的磁盘占用大小，按大小降序输出前 N 个包。

用法：
    python scripts/pkg_disk_usage.py
    python scripts/pkg_disk_usage.py --top 100
    python scripts/pkg_disk_usage.py --csv package_sizes.csv
"""

import argparse
import os
import sys
from importlib import metadata


def get_dir_size(path):
    """递归计算目录下所有文件的总大小（字节）"""
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def human_size(num_bytes):
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.2f} TB"


def main():
    parser = argparse.ArgumentParser(description="统计当前环境已安装包的磁盘占用大小")
    parser.add_argument("--top", type=int, default=50, help="显示前多少个包，默认50")
    parser.add_argument("--csv", type=str, default=None, help="可选，导出结果到指定csv文件")
    args = parser.parse_args()

    # site-packages 根目录（取第一个已安装分发的父目录的父目录作为基准更可靠，
    # 这里直接用 sys.prefix 拼出标准 venv 路径）
    site_packages_candidates = [
        p for p in sys.path if p.rstrip(os.sep).endswith("site-packages")
    ]
    if not site_packages_candidates:
        print("未能定位到 site-packages 目录，请确认已激活虚拟环境。")
        sys.exit(1)

    site_packages = site_packages_candidates[0]
    print(f"site-packages 路径: {site_packages}\n")

    results = []
    seen_locations = set()

    for dist in metadata.distributions():
        try:
            name = dist.metadata["Name"] or dist.metadata.get("Summary", "unknown")
        except Exception:
            name = str(dist._path)

        version = dist.version if dist.version else "?"

        # dist-info / egg-info 目录本身的大小（记录元数据、RECORD等）
        dist_info_path = str(dist._path) if hasattr(dist, "_path") else None
        size = 0
        counted_paths = set()

        if dist_info_path and os.path.isdir(dist_info_path):
            size += get_dir_size(dist_info_path)
            counted_paths.add(os.path.normcase(dist_info_path))

        # 通过 RECORD 文件找到该包实际安装的所有文件，累加体积
        # 这样可以把 xxx/ 目录和 xxx-x.x.x.dist-info/ 合并到同一个包名下
        try:
            files = dist.files or []
        except Exception:
            files = []

        top_level_dirs = set()
        for f in files:
            try:
                abs_path = dist.locate_file(f)
                abs_path_str = str(abs_path)
            except Exception:
                continue

            norm = os.path.normcase(os.path.abspath(abs_path_str))
            if norm in counted_paths:
                continue

            if os.path.isfile(abs_path_str):
                try:
                    size += os.path.getsize(abs_path_str)
                    counted_paths.add(norm)
                except OSError:
                    pass

        key = f"{name}=={version}"
        if key in seen_locations:
            continue
        seen_locations.add(key)

        results.append((name, version, size))

    results.sort(key=lambda x: x[2], reverse=True)
    top_results = results[: args.top]

    # 打印结果
    print(f"{'排名':<4} {'包名':<30} {'版本':<15} {'大小':>12}")
    print("-" * 65)
    for i, (name, version, size) in enumerate(top_results, 1):
        print(f"{i:<4} {name:<30} {version:<15} {human_size(size):>12}")

    total_size = sum(r[2] for r in results)
    print("-" * 65)
    print(f"共统计 {len(results)} 个包，总占用: {human_size(total_size)}")

    if args.csv:
        import csv

        with open(args.csv, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["排名", "包名", "版本", "大小(字节)", "大小(可读)"])
            for i, (name, version, size) in enumerate(top_results, 1):
                writer.writerow([i, name, version, size, human_size(size)])
        print(f"\n已导出到: {args.csv}")


if __name__ == "__main__":
    main()
