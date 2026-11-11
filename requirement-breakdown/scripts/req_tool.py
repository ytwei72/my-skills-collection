# -*- coding: utf-8 -*-
"""需求文档扫描与自检，成体系 / 单文件通用，存放路径不限。

用法：
    python .cursor/skills/requirement-breakdown/scripts/req_tool.py scan [路径]
    python .cursor/skills/requirement-breakdown/scripts/req_tool.py check <路径> [--fix-index]

scan   在路径下找已有需求体系（默认 docs/requirements），列出总览、条目模板、下一个编号、
       每条需求的状态与背景摘要、通用规格编号。名为「需求规范模板」的目录与 _ 开头的文件不算。
check  对路径下找到的每套体系做自检，有 FAIL 退出码 1。
       成体系：frontmatter、编号唯一无缺号、子编号引用已定义、目录内断链、台账与 frontmatter 一致、残留占位。
       单文件：编号、子编号引用、第 8 节台账与第 9 节需求一致、断链、残留占位。
       --fix-index 按 frontmatter 重写成体系的台账（单文件台账须手改）。
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

INDEX_BEGIN = "<!-- 台账:开始 -->"
INDEX_END = "<!-- 台账:结束 -->"
INDEX_BEGIN_LINE = re.compile(r"^<!-- 台账:开始 -->[ \t]*$", re.M)
INDEX_END_LINE = re.compile(r"^<!-- 台账:结束 -->[ \t]*$", re.M)

REQUIRED_FIELDS = ("id", "title", "status", "priority", "对外规格", "方案文档", "现状快照")
VALID_STATUS = {"待办", "部分落地", "已落地", "已归档", "作废"}
VALID_PRIORITY = {"P0", "P1", "P2", "P3", "—"}
OUTBOUND = re.compile(r"^(未纳入|待纳入 V\d+\.\d+|V\d+\.\d+（[^）]+）)$")
SNAPSHOT = re.compile(r"^(—|\d{4}-\d{2}-\d{2})$")

LINK = re.compile(r"\]\(([^)\s]+)\)")
SUB_REF = re.compile(r"(?<![A-Za-z0-9])R(\d+)\.(\d+[a-z]?)(?![0-9a-z])")
SUB_CELL = re.compile(r"R(\d+)\.(\d+[a-z]?)")
SPEC_CODE = re.compile(r"^#{2,3}\s+(?:([A-Z]\d+(?:\.\d+)?)\b|.*[（(]([A-Z]\d+(?:\.\d+)?)[）)]\s*$)", re.M)
SINGLE_ITEM = re.compile(r"^###\s+R(\d+)\s+(.+?)\s*$", re.M)
SINGLE_INDEX = re.compile(r"^##\s+\d+\.\s*需求台账", re.M)
PLACEHOLDER = re.compile(r"【[^】\n]{1,40}】")

SKIP_DIRS = {"需求规范模板"}
SPEC_DIR_NAME = "需求规格说明书"
BUNDLED_ITEM_TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "成体系" / "需求分析" / "需求" / "_模板-需求条目.md"

errors: list[str] = []
warnings: list[str] = []


def show(path: Path) -> str:
    try:
        return Path(os.path.relpath(path, Path.cwd())).as_posix()
    except ValueError:
        return path.as_posix()


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").replace("\r\n", "\n")
    except UnicodeDecodeError:
        errors.append(f"不是 UTF-8 编码 {show(path)}")
        return ""


def skipped(path: Path, base: Path) -> bool:
    parts = path.relative_to(base).parts
    return any(p in SKIP_DIRS or p.startswith("_") for p in parts)


def repo_root(start: Path) -> Path:
    for d in (start, *start.parents):
        if (d / ".git").exists():
            return d
    return Path.cwd()


def discover(base: Path) -> tuple[list[Path], list[Path]]:
    """返回（成体系总览文件，单文件需求规范）。"""
    candidates = [base] if base.is_file() else [
        md for md in sorted(base.rglob("*.md")) if not skipped(md, base)
    ]
    systems: list[Path] = []
    singles: list[Path] = []
    for md in candidates:
        text = read(md)
        if INDEX_BEGIN_LINE.search(text):
            systems.append(md)
        elif SINGLE_INDEX.search(text) and SINGLE_ITEM.search(text):
            singles.append(md)
    return systems, singles


def parse_frontmatter(text: str) -> dict[str, str] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    data: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, _, value = line.partition(":")
        data[key.strip()] = value.strip()
    return data


def defined_subs(text: str) -> set[str]:
    found: set[str] = set()
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cell = s.strip("|").split("|", 1)[0].strip()
        if SUB_CELL.fullmatch(cell):
            found.add(cell)
    return found


def summary_line(text: str, heading: str = "## 背景与目标", width: int = 60) -> str:
    idx = text.find(heading)
    if idx < 0:
        return ""
    for line in text[idx + len(heading):].splitlines():
        s = line.strip()
        if s.startswith("#"):
            return ""
        if s and not s.startswith(("|", ">", "<!--", "```")):
            return s if len(s) <= width else s[:width] + "…"
    return ""


def item_template(root: Path) -> Path | None:
    for p in (root / "_模板" / "需求条目.md", root / "需求" / "_模板-需求条目.md"):
        if p.exists():
            return p
    return None


def load_items(items_dir: Path, root_for_plan: Path, strict: bool) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    if not items_dir.is_dir():
        return items
    for md in sorted(items_dir.glob("*.md")):
        if md.name.startswith("_"):
            continue
        text = read(md)
        meta = parse_frontmatter(text)
        if meta is None:
            if strict:
                errors.append(f"缺 frontmatter {show(md)}")
            continue
        missing = [f for f in REQUIRED_FIELDS if not meta.get(f)]
        if missing:
            if strict:
                errors.append(f"frontmatter 缺字段 {show(md)}：{'、'.join(missing)}（无内容填 —）")
            continue
        if not re.fullmatch(r"R\d+", meta["id"]):
            if strict:
                errors.append(f"id 非法 {show(md)}：{meta['id']}")
            continue
        if strict:
            if meta["status"] not in VALID_STATUS:
                errors.append(f"status 非法 {show(md)}：{meta['status']}（可选 {'/'.join(sorted(VALID_STATUS))}）")
            if meta["priority"] not in VALID_PRIORITY:
                errors.append(f"priority 非法 {show(md)}：{meta['priority']}")
            if not OUTBOUND.fullmatch(meta["对外规格"]):
                errors.append(f"对外规格 取值非法 {show(md)}：{meta['对外规格']}（未纳入 / 待纳入 V1.x / V1.x（受众））")
            if not SNAPSHOT.fullmatch(meta["现状快照"]):
                errors.append(f"现状快照 取值非法 {show(md)}：{meta['现状快照']}（— 或 YYYY-MM-DD）")
            prefix = md.name.split("-", 1)[0]
            if not re.fullmatch(r"R\d+", prefix) or int(prefix[1:]) != int(meta["id"][1:]):
                errors.append(f"文件名编号与 id 不一致 {show(md)}：id={meta['id']}")
            plan = meta["方案文档"]
            if plan != "—" and not (root_for_plan / plan).exists():
                errors.append(f"方案文档不存在 {show(md)}：{plan}（写仓库内相对路径）")
        meta["_path"] = str(md)
        meta["_num"] = meta["id"][1:]
        meta["_text"] = text
        items.append(meta)
    return sorted(items, key=lambda m: int(m["_num"]))


def check_numbers(nums: list[int], where: str) -> None:
    seen: set[int] = set()
    for n in nums:
        if n in seen:
            errors.append(f"需求编号重复 R{n}（{where}）")
        seen.add(n)
    if seen:
        gaps = [n for n in range(1, max(seen) + 1) if n not in seen]
        if gaps:
            errors.append(f"需求编号缺号（{where}）：{'、'.join(f'R{n}' for n in gaps)}")


def check_file_body(md: Path, text: str, known: set[int], defined: set[str]) -> None:
    # 模板里讲编号写法的行用 R4.5 之类作示例，不算真实引用
    body = "\n".join(line for line in text.splitlines() if "交叉引用" not in line)
    for major, minor in SUB_REF.findall(body):
        if int(major) in known and f"R{major}.{minor}" not in defined:
            errors.append(f"引用了未定义的子编号 {show(md)}：R{major}.{minor}")
    for target in LINK.findall(text):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        path = target.split("#", 1)[0].strip("`")
        if path and not (md.parent / path).resolve().exists():
            errors.append(f"断链 {show(md)} -> {target}")
    if SPEC_DIR_NAME not in md.parts:
        hits = sorted(set(PLACEHOLDER.findall(text)))
        if hits:
            warnings.append(f"残留模板占位 {show(md)}：{'、'.join(hits[:5])}{' 等' if len(hits) > 5 else ''}")


def build_index(items: list[dict[str, str]], index_file: Path, root: Path) -> str:
    lines = [
        "| 编号 | 需求 | 状态 | 优先级 | 对外规格 | 方案文档 |",
        "|------|------|------|--------|----------|----------|",
    ]
    for m in items:
        href = Path(os.path.relpath(m["_path"], index_file.parent)).as_posix()
        plan = m["方案文档"]
        if plan == "—":
            plan_cell = "—"
        else:
            plan_href = Path(os.path.relpath(root / plan, index_file.parent)).as_posix()
            plan_cell = f"[{Path(plan).stem}]({plan_href})"
        lines.append(
            f"| [{m['id']}]({href}) | {m['title']} | {m['status']} | "
            f"{m['priority']} | {m['对外规格']} | {plan_cell} |"
        )
    return "\n".join(lines)


def check_system(index_file: Path, fix: bool) -> int:
    root = index_file.parent
    repo = repo_root(root)
    items = load_items(root / "需求", repo, strict=True)
    check_numbers([int(m["_num"]) for m in items], show(root))
    known = {int(m["_num"]) for m in items}
    defined: set[str] = set()
    for m in items:
        defined |= defined_subs(m["_text"])
    scope = root.parent if root.name == "需求分析" else root
    for md in sorted(scope.rglob("*.md")):
        if not skipped(md, scope):
            check_file_body(md, read(md), known, defined)

    text = read(index_file)
    begin = INDEX_BEGIN_LINE.search(text)
    end = INDEX_END_LINE.search(text, begin.end()) if begin else None
    if not begin or not end:
        errors.append(f"{show(index_file)} 缺台账标记 {INDEX_BEGIN} / {INDEX_END}（各占一行）")
        return len(items)
    expected = build_index(items, index_file, repo)
    if text[begin.end():end.start()].strip() != expected:
        if fix:
            new = text[: begin.end()] + "\n" + expected + "\n" + text[end.start():]
            index_file.write_text(new, encoding="utf-8", newline="\n")
            print(f"已重写需求台账：{show(index_file)}")
        else:
            errors.append(f"台账与 frontmatter 不一致，加 --fix-index 重新生成：{show(index_file)}")
    return len(items)


def parse_single(text: str) -> tuple[dict[int, str], list[list[str]]]:
    heads: dict[int, str] = {}
    nums: list[int] = []
    for num, title in SINGLE_ITEM.findall(text):
        nums.append(int(num))
        heads[int(num)] = title.strip()
    check_numbers(nums, "第 9 节需求标题")
    rows: list[list[str]] = []
    m = SINGLE_INDEX.search(text)
    if m:
        section = text[m.end():]
        nxt = re.search(r"^## ", section, re.M)
        section = section[: nxt.start()] if nxt else section
        for line in section.splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if line.strip().startswith("|") and cells and re.search(r"R\d+", cells[0]) and "编号" not in cells[0]:
                rows.append(cells)
    return heads, rows


def check_single(md: Path) -> int:
    text = read(md)
    heads, rows = parse_single(text)
    listed: dict[int, list[str]] = {}
    for cells in rows:
        num = int(re.search(r"R(\d+)", cells[0]).group(1))
        listed[num] = cells
        if len(cells) < 5:
            errors.append(f"台账行列数不足 {show(md)}：{cells[0]}")
            continue
        if cells[2] not in VALID_STATUS:
            errors.append(f"台账 status 非法 {show(md)}：R{num} {cells[2]}")
        if cells[3] not in VALID_PRIORITY:
            errors.append(f"台账 priority 非法 {show(md)}：R{num} {cells[3]}")
        if not OUTBOUND.fullmatch(cells[4]):
            errors.append(f"台账 对外规格 非法 {show(md)}：R{num} {cells[4]}")
    for num in sorted(set(heads) - set(listed)):
        errors.append(f"第 9 节有 R{num}，台账里没有 {show(md)}")
    for num in sorted(set(listed) - set(heads)):
        errors.append(f"台账有 R{num}，第 9 节没有 {show(md)}")
    for num in sorted(set(heads) & set(listed)):
        if listed[num][1] != heads[num]:
            errors.append(f"台账名称与标题不一致 {show(md)}：R{num}「{listed[num][1]}」≠「{heads[num]}」")
    check_file_body(md, text, set(heads), defined_subs(text))
    return len(heads)


def cmd_scan(base: Path) -> int:
    systems, singles = discover(base)
    if not systems and not singles:
        print(f"{show(base)} 下没有已有需求体系，按模板新建")
        return 0
    for index_file in systems:
        root = index_file.parent
        items = load_items(root / "需求", repo_root(root), strict=False)
        nxt = max((int(m["_num"]) for m in items), default=0) + 1
        tpl = item_template(root)
        print(f"[成体系] {show(root)}")
        print(f"  总览：{show(index_file)}")
        print(f"  条目模板：{show(tpl) if tpl else f'无（用 {show(BUNDLED_ITEM_TEMPLATE)}）'}")
        print(f"  下一个编号：R{nxt}（文件名 R{nxt:02d}-标题.md）")
        print("  需求：")
        for m in items:
            subs = defined_subs(m["_text"])
            print(
                f"    {m['id']:<4} {m['title']} | {m['status']} | {m['priority']} | "
                f"子编号 {len(subs)} | {Path(m['_path']).name}"
            )
            line = summary_line(m["_text"])
            if line:
                print(f"         {line}")
        spec_dir = root / "通用规格"
        if spec_dir.is_dir():
            print("  通用规格：")
            for md in sorted(spec_dir.glob("*.md")):
                if md.name == "README.md":
                    continue
                codes = [a or b for a, b in SPEC_CODE.findall(read(md))]
                print(f"    {md.name}  {' '.join(codes) if codes else '（无编号小节）'}")
        print()
    for md in singles:
        heads, _ = parse_single(read(md))
        nxt = max(heads, default=0) + 1
        print(f"[单文件] {show(md)}")
        print(f"  下一个编号：R{nxt}")
        for num, title in sorted(heads.items()):
            print(f"    R{num:<3} {title}")
        print()
    return 0


def cmd_check(base: Path, fix: bool) -> int:
    systems, singles = discover(base)
    if not systems and not singles:
        print(f"[FAIL] {show(base)} 下没有找到需求体系（成体系须有台账标记，单文件须有「N. 需求台账」与「### RN」）")
        return 1
    total = 0
    for index_file in systems:
        total += check_system(index_file, fix)
    for md in singles:
        total += check_single(md)
    for msg in warnings:
        print(f"[WARN] {msg}")
    if errors:
        for msg in errors:
            print(f"[FAIL] {msg}")
        print(f"\n共 {len(errors)} 项不通过")
        return 1
    print(f"体系 {len(systems) + len(singles)} 套，需求 {total} 条，全部检查通过")
    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_scan = sub.add_parser("scan", help="列出已有需求体系")
    p_scan.add_argument("path", nargs="?", default="docs/requirements")
    p_check = sub.add_parser("check", help="自检")
    p_check.add_argument("path")
    p_check.add_argument("--fix-index", action="store_true", help="按 frontmatter 重写成体系台账")
    args = parser.parse_args()

    base = Path(args.path).resolve()
    if not base.exists():
        print(f"{show(base)} 不存在，按模板新建" if args.cmd == "scan" else f"[FAIL] 路径不存在 {args.path}")
        return 0 if args.cmd == "scan" else 1
    if args.cmd == "scan":
        return cmd_scan(base)
    return cmd_check(base, args.fix_index)


if __name__ == "__main__":
    raise SystemExit(main())
