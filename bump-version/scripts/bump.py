"""递增当前仓库 VERSION / BUILD，并同步前后端版本常量。

在业务仓库根目录执行（脚本在共享技能库，通过 Junction 挂到
`.cursor/skills/bump-version/scripts/bump.py`）：

    uv run python .cursor/skills/bump-version/scripts/bump.py
    uv run python .cursor/skills/bump-version/scripts/bump.py --minor
    uv run python .cursor/skills/bump-version/scripts/bump.py --major
    uv run python .cursor/skills/bump-version/scripts/bump.py --patch
    uv run python .cursor/skills/bump-version/scripts/bump.py --set 1.0.0
    uv run python .cursor/skills/bump-version/scripts/bump.py --set 1.0.0 --build 200
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
VERSION_ASSIGN = re.compile(r'^VERSION = "(\d+\.\d+\.\d+)"$', re.M)
BUILD_ASSIGN = re.compile(r"^BUILD = (\d+)$", re.M)


def die(message: str, code: int = 1) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def find_repo_root() -> Path:
    """定位业务仓库根目录。

    技能经 Junction 挂载时，``Path(__file__).resolve()`` 会落到共享库，
    不能再按脚本路径往上数。优先用 cwd / git toplevel。
    """
    start = Path.cwd().resolve()
    candidates: list[Path] = []
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=start,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            candidates.append(Path(proc.stdout.strip()))
    except OSError:
        pass
    candidates.extend([start, *start.parents])

    seen: set[Path] = set()
    for root in candidates:
        root = root.resolve()
        if root in seen:
            continue
        seen.add(root)
        if (root / "app" / "core" / "app_version.py").is_file():
            return root
    die("找不到版本源 app/core/app_version.py，请在业务仓库根目录执行")


ROOT = find_repo_root()
APP_VERSION_PY = ROOT / "app" / "core" / "app_version.py"
APP_VERSION_TS = ROOT / "frontend" / "src" / "config" / "appVersion.ts"
PYPROJECT = ROOT / "pyproject.toml"
PACKAGE_JSON = ROOT / "frontend" / "package.json"
PACKAGE_LOCK = ROOT / "frontend" / "package-lock.json"


def read_text(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    newline = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return text, newline


def write_text(path: Path, text: str, newline: str) -> None:
    normalized = text.replace("\r\n", "\n").replace("\n", newline)
    path.write_bytes(normalized.encode("utf-8"))


def replace_once(path: Path, pattern: re.Pattern[str], repl: str) -> None:
    text, newline = read_text(path)
    new, n = pattern.subn(repl, text, count=1)
    if n != 1:
        die(f"更新失败 {path.relative_to(ROOT)}: 期望匹配 1 次，实际 {n}")
    write_text(path, new, newline)


def parse_semver(value: str) -> tuple[int, int, int]:
    match = SEMVER.match(value)
    if not match:
        die(f"版本号必须是 X.Y.Z，收到: {value}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def format_semver(parts: tuple[int, int, int]) -> str:
    return f"{parts[0]}.{parts[1]}.{parts[2]}"


def read_current() -> tuple[str, int]:
    if not APP_VERSION_PY.is_file():
        die(f"找不到版本源文件: {APP_VERSION_PY}")
    text, _ = read_text(APP_VERSION_PY)
    version_match = VERSION_ASSIGN.search(text)
    build_match = BUILD_ASSIGN.search(text)
    if not version_match or not build_match:
        die(f"无法从 {APP_VERSION_PY.relative_to(ROOT)} 解析 VERSION / BUILD")
    return version_match.group(1), int(build_match.group(1))


def next_version(current: str, mode: str, explicit: str | None) -> str:
    if mode == "set":
        assert explicit is not None
        parse_semver(explicit)
        return explicit
    major, minor, patch = parse_semver(current)
    if mode == "major":
        return format_semver((major + 1, 0, 0))
    if mode == "minor":
        return format_semver((major, minor + 1, 0))
    if mode == "patch":
        return format_semver((major, minor, patch + 1))
    return current


def next_build(current: int, explicit: int | None) -> int:
    if explicit is None:
        return current + 1
    if explicit < 1:
        die("BUILD 必须是正整数")
    return explicit


def update_files(old_version: str, new_version: str, new_build: int) -> list[str]:
    updated: list[str] = []

    replace_once(APP_VERSION_PY, VERSION_ASSIGN, f'VERSION = "{new_version}"')
    replace_once(APP_VERSION_PY, BUILD_ASSIGN, f"BUILD = {new_build}")
    updated.append(str(APP_VERSION_PY.relative_to(ROOT)).replace("\\", "/"))

    replace_once(
        APP_VERSION_TS,
        re.compile(r"^export const APP_VERSION = '[^']+'$", re.M),
        f"export const APP_VERSION = '{new_version}'",
    )
    replace_once(
        APP_VERSION_TS,
        re.compile(r"^export const APP_BUILD = \d+$", re.M),
        f"export const APP_BUILD = {new_build}",
    )
    updated.append(str(APP_VERSION_TS.relative_to(ROOT)).replace("\\", "/"))

    if new_version != old_version:
        replace_once(
            PYPROJECT,
            re.compile(r'^version = "[^"]+"$', re.M),
            f'version = "{new_version}"',
        )
        updated.append(str(PYPROJECT.relative_to(ROOT)).replace("\\", "/"))

        replace_once(
            PACKAGE_JSON,
            re.compile(r'^(\s*)"version": "[^"]+"', re.M),
            rf'\1"version": "{new_version}"',
        )
        updated.append(str(PACKAGE_JSON.relative_to(ROOT)).replace("\\", "/"))

        if PACKAGE_LOCK.is_file():
            lock_text, lock_nl = read_text(PACKAGE_LOCK)
            lock_new, n = re.subn(
                rf'^(\s*)"version": "{re.escape(old_version)}"',
                rf'\1"version": "{new_version}"',
                lock_text,
                count=2,
                flags=re.M,
            )
            if n:
                write_text(PACKAGE_LOCK, lock_new, lock_nl)
                updated.append(str(PACKAGE_LOCK.relative_to(ROOT)).replace("\\", "/"))

    return updated


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="递增仓库 VERSION / BUILD")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--major", action="store_true", help="大版本 +1，小版本与补丁归零")
    group.add_argument("--minor", action="store_true", help="小版本 +1，补丁归零")
    group.add_argument("--patch", action="store_true", help="补丁号 +1")
    group.add_argument("--set", metavar="X.Y.Z", help="指定版本号")
    parser.add_argument("--build", type=int, help="指定 BUILD；省略则当前 BUILD +1")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.major:
        mode = "major"
    elif args.minor:
        mode = "minor"
    elif args.patch:
        mode = "patch"
    elif args.set:
        mode = "set"
    else:
        mode = "build"

    old_version, old_build = read_current()
    new_version = next_version(old_version, mode, args.set)
    new_build = next_build(old_build, args.build)

    if new_version == old_version and new_build == old_build:
        die(f"版本未变化，仍是 {old_version} ({old_build})")
    if new_build < old_build:
        die(f"BUILD 不能回退：当前 {old_build}，目标 {new_build}")

    updated = update_files(old_version, new_version, new_build)
    print(f"{old_version} ({old_build}) -> {new_version} ({new_build})")
    for path in updated:
        print(f"updated: {path}")


if __name__ == "__main__":
    main()
