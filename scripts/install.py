#!/usr/bin/env python3
"""把 Quiver 里的 skill 安装到 Agent 客户端的 skills 目录。

用法：
    python scripts/install.py <skill-name>...      # 安装指定 skill
    python scripts/install.py --all                # 安装全部
    python scripts/install.py --all --client workbuddy
    python scripts/install.py jd-decoder --target /some/dir

客户端默认安装位置：
    claude    -> ~/.claude/skills/
    workbuddy -> ~/.workbuddy/skills/
也可用 --target 显式指定目录（优先级最高）。
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"

CLIENT_DIRS = {
    "claude": Path.home() / ".claude" / "skills",
    "workbuddy": Path.home() / ".workbuddy" / "skills",
}


def available_skills() -> list[str]:
    if not SKILLS_DIR.is_dir():
        return []
    return sorted(
        d.name
        for d in SKILLS_DIR.iterdir()
        if d.is_dir() and (d / "SKILL.md").is_file()
    )


def resolve_target(args: argparse.Namespace) -> Path:
    if args.target:
        return Path(args.target).expanduser()
    if args.client in CLIENT_DIRS:
        return CLIENT_DIRS[args.client]
    raise SystemExit(f"未知客户端: {args.client!r}（可选: claude / workbuddy）")


def install_one(name: str, target_dir: Path, force: bool) -> bool:
    src = SKILLS_DIR / name
    if not (src / "SKILL.md").is_file():
        print(f"SKIP  {name}: 不存在（可用: {', '.join(available_skills())}）")
        return False
    dest = target_dir / name
    if dest.exists():
        if not force:
            print(f"SKIP  {name}: 目标已存在 {dest}（--force 覆盖）")
            return False
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    print(f"OK    {name} -> {dest}")
    return True


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="安装 Quiver skills 到客户端目录")
    parser.add_argument("names", nargs="*", help="要安装的 skill 名（或 --all）")
    parser.add_argument("--all", action="store_true", help="安装全部 skill")
    parser.add_argument(
        "--client", choices=sorted(CLIENT_DIRS), default="claude",
        help="目标客户端（默认 claude）",
    )
    parser.add_argument("--target", help="显式目标目录（覆盖 --client）")
    parser.add_argument("--force", action="store_true", help="覆盖已存在的安装")
    args = parser.parse_args(argv[1:])

    if args.all:
        names = available_skills()
        if not names:
            print("没有可安装的 skill", file=sys.stderr)
            return 2
    elif args.names:
        names = args.names
    else:
        parser.print_usage()
        print("\n请提供 skill 名或 --all", file=sys.stderr)
        return 2

    target = resolve_target(args)
    target.mkdir(parents=True, exist_ok=True)
    ok = sum(install_one(n, target, args.force) for n in names)
    print(f"\n{ok}/{len(names)} 个 skill 已安装到 {target}")
    return 0 if ok == len(names) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
