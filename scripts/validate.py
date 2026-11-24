# -*- coding: utf-8 -*-
"""校验 skills/ 目录下所有 Agent Skill 的 SKILL.md 是否合规。

规则（对齐主流客户端加载器的常见约束）：
- 必须有 YAML frontmatter（首行为 ---，且存在闭合 ---）；
- 必填字段：name、description；
- name：小写字母/数字/连字符，长度 1-64，且必须与所在目录名一致；
- description：非空，长度 <= 1024；
- 正文长度 >= 200 字符（防止占位文件）；
- 正文不得包含 TODO / 待补充 / FIXME 占位标记。

另外校验分发产物（这几条是给「装不上」和「索引说漏了」两类真实故障用的）：
- `.agents/skills/<name>/SKILL.md` 必须与 `skills/<name>/SKILL.md` 逐字节一致，
  否则两个客户端会加载到不同版本，且没人会发现；
- SKILLS.md 里出现的每个 skill 名必须真实存在，且每个 skill 都必须出现在 SKILLS.md；
- 各客户端入口目录的文件数必须等于 skill 数。

用法：
    python scripts/validate.py            # 校验 skills/ 全部
    python scripts/validate.py <dir>...   # 校验指定 skill 目录
"""

from __future__ import annotations

import io
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
DESCRIPTION_MAX = 1024
BODY_MIN = 200
PLACEHOLDER_WORDS = ("TODO", "FIXME", "待补充", "待完善")

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"


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
            raise ValueError(f"frontmatter 行缺少字段名: {line!r}")
        fields[key] = value
    body = "\n".join(lines[end + 1:])
    return fields, body


def check_skill(skill_dir: Path) -> list[str]:
    """返回该 skill 的问题列表，空列表表示通过。

    旧名字 validate_skill 保留为别名：测试与外部脚本都在用，
    改实现不该顺带改掉别人依赖的名字。
    """
    problems: list[str] = []
    path = skill_dir / "SKILL.md"
    if not path.is_file():
        return [f"缺少 SKILL.md：{path}"]
    text = io.open(path, encoding="utf-8").read()
    try:
        fields, body = parse_frontmatter(text)
    except ValueError as exc:
        return [str(exc)]

    name = fields.get("name", "")
    if not name:
        problems.append("缺少必填字段 name")
    elif not NAME_RE.match(name):
        problems.append(f"name 不合规（只能小写字母/数字/连字符，1-64）: {name!r}")
    elif name != skill_dir.name:
        problems.append(f"name 与目录名不一致：{name!r} != {skill_dir.name!r}")

    desc = fields.get("description", "")
    if not desc:
        problems.append("缺少 description（必填）")
    elif len(desc) > DESCRIPTION_MAX:
        problems.append(f"description 超过上限：{len(desc)} > {DESCRIPTION_MAX}")

    extra = sorted(set(fields) - {"name", "description"})
    if extra:
        problems.append(f"含扩展字段 frontmatter：{', '.join(extra)}（换客户端可能不认）")

    if len(body.strip()) < BODY_MIN:
        problems.append(f"正文过短：{len(body.strip())} < {BODY_MIN}")
    for word in PLACEHOLDER_WORDS:
        if word in body:
            problems.append(f"正文含占位标记：{word}")
    return problems


def check_distribution() -> list[str]:
    """校验分发产物与 skills/ 是否一致。"""
    problems: list[str] = []
    skills = [p.name for p in discover_skill_dirs()]

    agents = ROOT / ".agents" / "skills"
    if not agents.is_dir():
        return ["缺少 .agents/skills/，先跑 scripts/distribute.py"]
    for name in skills:
        mirror = agents / name / "SKILL.md"
        src = SKILLS_DIR / name / "SKILL.md"
        if not mirror.is_file():
            problems.append(f".agents/skills/{name}/SKILL.md 缺失")
        elif mirror.read_bytes() != src.read_bytes():
            problems.append(f".agents/skills/{name}/SKILL.md 与源文件不一致（客户端会加载到旧版本）")

    index = ROOT / "SKILLS.md"
    if not index.is_file():
        problems.append("缺少 SKILLS.md")
    else:
        listed = set(re.findall(r"^\| `([a-z0-9-]+)` \|", index.read_text(encoding="utf-8"), re.M))
        for missing in sorted(set(skills) - listed):
            problems.append(f"SKILLS.md 漏了这个 skill：{missing}（读者会以为它不存在）")
        for extra in sorted(listed - set(skills)):
            problems.append(f"SKILLS.md 提到了不存在的 skill：{extra}")

    for label, rel in (
        ("cursor", ".cursor/rules"),
        ("cline", ".clinerules"),
        ("gemini", ".gemini/commands"),
    ):
        d = ROOT / rel
        count = len(list(d.glob("*"))) if d.is_dir() else 0
        if count != len(skills):
            problems.append(f"{label} 入口文件数 {count} != skill 数 {len(skills)}")
    return problems


def discover_skill_dirs(roots: Path | list[Path] | None = None) -> list[Path]:
    """列出 roots 下所有含 SKILL.md 的子目录（返回 Path，不是名字）。

    只认「有 SKILL.md」的目录：一个空的或只有 README 的目录不是 skill，
    把它当成 skill 会在校验时报「缺少 SKILL.md」，掩盖真正的问题。
    不传参时扫仓库自带的 skills/；单传一个 skill 目录时它本身就是结果。
    """
    """列出 root 下所有含 SKILL.md 的子目录名。

    只认「有 SKILL.md」的目录：一个空的或只有 README 的目录不是 skill，
    把它当成 skill 会在校验时报「缺少 SKILL.md」，掩盖真正的问题。
    """
    if roots is None:
        roots = [SKILLS_DIR]
    elif isinstance(roots, Path):
        roots = [roots]
    found: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        if (root / "SKILL.md").is_file():
            found.append(root)          # 直接传了一个 skill 目录
            continue
        found.extend(sorted(p for p in root.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()))
    return found


def main(argv: list[str]) -> int:
    targets = [Path(a) for a in argv[1:]] or discover_skill_dirs()
    failed = 0
    for d in targets:
        problems = check_skill(d)
        if problems:
            failed += 1
            print(f"FAIL  {d.name}")
            for p in problems:
                print(f"      - {p}")
        else:
            print(f"OK    {d.name}")

    if not argv[1:]:
        dist_problems = check_distribution()
        if dist_problems:
            failed += 1
            print("FAIL  分发产物")
            for p in dist_problems:
                print(f"      - {p}")
        else:
            print("OK    分发产物（.agents / SKILLS.md / 三处入口）")

    total = len(targets) + (1 if not argv[1:] else 0)
    print(f"\n{total - failed}/{total} 通过校验")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))


# 旧名字保留：外部脚本和测试按这两个名字调用，改实现不该改掉别人的接口。
validate_skill = check_skill
