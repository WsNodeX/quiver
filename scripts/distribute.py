# -*- coding: utf-8 -*-
"""把 quiver 改造成多客户端分发的形态。

做三件事，每件都为了一个具体的读者问题：
1. 把每个 skill 拆到 `.agents/skills/<name>/`（Claude Code / Codex / Cursor / Gemini CLI
   都能从这个位置发现），同时保留旧路径不动，避免已装用户断掉。
2. 生成各客户端的入口文件（插件清单、规则文件、命令文件）。
3. 生成一份 skill 索引，README 和校验器共用。
"""

from __future__ import annotations

import io
import json
import os
import shutil
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
SKILLS = ROOT / "skills"

# 13 个 skill 的阶段分组：给读者「我现在在哪一步」的定位，而不是一张 13 行的平表。
STAGES = [
    ("定位", ["quiver-router"], "先搞清楚现在该做什么，别一次装 13 个"),
    ("读懂岗位", ["jd-decoder", "jd-reverse"], "JD 真正在要什么，以及你想去的方向需要什么"),
    ("材料", ["resume-reviewer", "readme-booster"], "把简历和项目页改到陌生人愿意看完"),
    ("模拟面试", ["interview-grill", "grill-java", "behavioral-coach"], "技术面、八股、HR 面分开打"),
    ("实战", ["take-home-reviewer"], "笔试和 take-home 的返工检查"),
    ("收尾", ["offer-compare", "salary-negotiator", "intern-defense"], "比 offer、谈薪、实习转正答辩"),
    ("日常", ["weekly-report"], "周报不是汇报，是留证据"),
]

CLIENTS = [
    # (客户端, 目录, 入口文件名, 说明)
    ("Claude Code", "claude", "SKILL.md", "plugins 方式：.claude-plugin/plugin.json"),
    ("Codex CLI", "codex", "SKILL.md", "AGENTS.md 里引用 .agents/skills/"),
    ("Cursor", "cursor", "SKILL.md", ".cursor/rules/*.mdc"),
    ("Cline", "cline", "SKILL.md", ".clinerules/"),
    ("Gemini CLI", "gemini", "SKILL.md", ".gemini/commands/*.toml"),
    ("通用 Agent", "agents", "SKILL.md", ".agents/skills/<name>/SKILL.md"),
]


def read_frontmatter(path: Path) -> dict:
    lines = io.open(path, encoding="utf-8").read().splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path}: 缺少 frontmatter")
    end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    fields = {}
    for raw in lines[1:end]:
        if ":" not in raw:
            continue
        key, _, value = raw.partition(":")
        fields[key.strip()] = value.strip().strip("'\"")
    return fields


def main() -> int:
    skill_dirs = sorted(p for p in SKILLS.iterdir() if p.is_dir())
    meta = {}
    for d in skill_dirs:
        meta[d.name] = read_frontmatter(d / "SKILL.md")

    # ---- 1. 通用发现路径 -------------------------------------------------
    agents_dir = ROOT / ".agents" / "skills"
    if agents_dir.exists():
        shutil.rmtree(agents_dir)
    for d in skill_dirs:
        target = agents_dir / d.name
        target.mkdir(parents=True, exist_ok=True)
        shutil.copy2(d / "SKILL.md", target / "SKILL.md")
    print(f".agents/skills/: {len(skill_dirs)} 个")

    # ---- 2. 各客户端入口 -------------------------------------------------
    plugin = {
        "name": "quiver",
        "description": "13 个求职 Agent Skills：读懂 JD、改简历、模拟面试、谈薪、周报",
        "version": "1.1.0",
        "skills": "./.agents/skills",
    }
    (ROOT / ".claude-plugin").mkdir(exist_ok=True)
    io.open(ROOT / ".claude-plugin" / "plugin.json", "w", encoding="utf-8").write(
        json.dumps(plugin, ensure_ascii=False, indent=2) + "\n"
    )

    (ROOT / ".codex-plugin").mkdir(exist_ok=True)
    io.open(ROOT / ".codex-plugin" / "plugin.json", "w", encoding="utf-8").write(
        json.dumps(plugin, ensure_ascii=False, indent=2) + "\n"
    )

    # Cursor 用 .mdc 规则文件：每个 skill 一个，description 里的触发条件直接写进 frontmatter
    rules = ROOT / ".cursor" / "rules"
    rules.mkdir(parents=True, exist_ok=True)
    for name, f in meta.items():
        body = io.open(SKILLS / name / "SKILL.md", encoding="utf-8").read()
        io.open(rules / f"{name}.mdc", "w", encoding="utf-8").write(
            f"---\ndescription: {f['description']}\nglobs:\nalwaysApply: false\n---\n\n{body}\n"
        )

    # Cline 只认根目录 .clinerules/ 下的 Markdown
    clinerules = ROOT / ".clinerules"
    clinerules.mkdir(exist_ok=True)
    for name, f in meta.items():
        body = io.open(SKILLS / name / "SKILL.md", encoding="utf-8").read()
        io.open(clinerules / f"{name}.md", "w", encoding="utf-8").write(
            f"# {name}\n\n{f['description']}\n\n{body}\n"
        )

    # Gemini CLI 用 TOML 命令
    gem = ROOT / ".gemini" / "commands"
    gem.mkdir(parents=True, exist_ok=True)
    for name, f in meta.items():
        io.open(gem / f"{name}.toml", "w", encoding="utf-8").write(
            f'description = "{f["description"][:200]}"\n'
            f'prompt = """\n{io.open(SKILLS / name / "SKILL.md", encoding="utf-8").read()}\n"""\n'
        )

    print(f"客户端入口: claude-plugin / codex-plugin / cursor({len(meta)}) / cline({len(meta)}) / gemini({len(meta)})")

    # ---- 3. 索引 ---------------------------------------------------------
    rows = []
    seen = set()
    for stage, names, note in STAGES:
        for n in names:
            if n not in meta:
                raise SystemExit(f"STAGES 引用了不存在的 skill: {n}")
            rows.append((stage, n, meta[n]["description"], note))
            seen.add(n)
    missing = set(meta) - seen
    if missing:
        raise SystemExit(f"这些 skill 没进 STAGES，README 会漏掉它们: {sorted(missing)}")

    lines = ["# Skill 索引", "", "按「你现在的处境」分组，不是按字母序。", ""]
    for stage, names, note in STAGES:
        lines.append(f"## {stage}")
        lines.append("")
        lines.append(f"*{note}*")
        lines.append("")
        lines.append("| Skill | 什么时候用 |")
        lines.append("|---|---|")
        for n in names:
            lines.append(f"| `{n}` | {meta[n]['description'].split('：')[0] if '：' in meta[n]['description'] else meta[n]['description'][:60]} |")
        lines.append("")
    io.open(ROOT / "SKILLS.md", "w", encoding="utf-8").write("\n".join(lines))
    print(f"SKILLS.md: {len(rows)} 个 skill，{len(STAGES)} 个阶段")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())