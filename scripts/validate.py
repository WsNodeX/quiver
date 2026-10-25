#!/usr/bin/env python3
"""校验 skills/ 目录下所有 Agent Skill 的 SKILL.md 是否合规。

规则（对齐主流客户端加载器的常见约束）：
- 必须有 YAML frontmatter（首行为 ---，且存在闭合 ---）；
- 必填字段：name、description；
- name：小写字母/数字/连字符，长度 1-64，且必须与所在目录名一致；
- description：非空，长度 <= 1024；
- 正文长度 >= 200 字符（防止占位文件）；
- 正文不得包含 TODO / 待补充 / FIXME 占位标记。

用法：
    python scripts/validate.py            # 校验 skills/ 全部
    python scripts/validate.py <dir>...   # 校验指定 skill 目录
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
DESCRIPTION_MAX = 1024
BODY_MIN = 200
PLACEHOLDER_WORDS = ("TODO", "FIXME", "待补充", "待完善")

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """从文本中解析 YAML frontmatter，返回 (字段字典, 正文)。

    手写解析只支持顶层 `key: value`，避免引入任何 YAML 依赖。
    frontmatter 不合法时抛出 ValueError。
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("缺少 frontmatter（首行必须是 '---'）")
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        raise ValueError("frontmatter 未闭合（缺少第二个 '---'）")

    fields: dict[str, str] = {}
    for raw in lines[1:end]:
        line = raw.rstrip()
        if not line.strip():
            continue
        if line[:1] in (" ", "\t"):
            raise ValueError("frontmatter 不支持嵌套字段（顶层 key: value）")
        if ":" not in line:
            raise ValueError(f"frontmatter 行缺少冒号: {line!r}")
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip().strip("'\"")
        if not key:
            raise ValueError("frontmatter 存在空 key")
        fields[key] = value
    body = "\n".join(lines[end + 1:])
    return fields, body


def validate_skill(skill_dir: Path) -> list[str]:
    """校验单个 skill 目录，返回问题列表（空列表 = 通过）。"""
    problems: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [f"{skill_dir.name}: 缺少 SKILL.md"]

    text = skill_md.read_text(encoding="utf-8")
    try:
        fields, body = parse_frontmatter(text)
    except ValueError as e:
        return [f"{skill_dir.name}: {e}"]

    name = fields.get("name")
    if not name:
        problems.append(f"{skill_dir.name}: frontmatter 缺少 name")
    elif not NAME_RE.match(name):
        problems.append(
            f"{skill_dir.name}: name {name!r} 不合规（需小写字母/数字/连字符，"
            f"长度 1-64）"
        )
    elif name != skill_dir.name:
        problems.append(
            f"{skill_dir.name}: name {name!r} 与目录名不一致"
        )

    description = fields.get("description")
    if not description:
        problems.append(f"{skill_dir.name}: frontmatter 缺少 description")
    elif len(description) > DESCRIPTION_MAX:
        problems.append(
            f"{skill_dir.name}: description 长度 {len(description)} "
            f"超过上限 {DESCRIPTION_MAX}"
        )

    extra = sorted(set(fields) - {"name", "description"})
    if extra:
        # 允许扩展字段，但报告出来便于人工确认
        problems.append(f"{skill_dir.name}: 存在扩展字段 {extra}（允许，请确认）")

    body_stripped = body.strip()
    if len(body_stripped) < BODY_MIN:
        problems.append(
            f"{skill_dir.name}: 正文过短（{len(body_stripped)} < {BODY_MIN} 字符）"
        )
    for word in PLACEHOLDER_WORDS:
        if word in text:
            problems.append(f"{skill_dir.name}: 含占位标记 {word!r}")

    return problems


def discover_skill_dirs(roots: list[Path] | None = None) -> list[Path]:
    dirs = roots if roots else [SKILLS_DIR]
    out: list[Path] = []
    for d in dirs:
        if d.name == "SKILL.md":
            d = d.parent
        if (d / "SKILL.md").is_file():
            out.append(d)
            continue
        if d.is_dir():
            for child in sorted(d.iterdir()):
                if (child / "SKILL.md").is_file():
                    out.append(child)
    return out


def main(argv: list[str]) -> int:
    roots = [Path(a) for a in argv[1:]]
    skill_dirs = discover_skill_dirs(roots)
    if not skill_dirs:
        print("没有找到任何 skill 目录（需要 <dir>/SKILL.md）", file=sys.stderr)
        return 2

    failed = 0
    for d in skill_dirs:
        problems = validate_skill(d)
        if problems:
            failed += 1
            print(f"FAIL  {d.name}")
            for p in problems:
                print(f"      - {p}")
        else:
            print(f"OK    {d.name}")

    total = len(skill_dirs)
    print(f"\n{total - failed}/{total} 个 skill 通过校验")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
