"""validate.py 的单元测试。"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import validate  # noqa: E402


def make_skill(tmp: Path, name: str, frontmatter: str, body: str) -> Path:
    d = tmp / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(
        f"---\n{frontmatter}\n---\n\n{body}\n", encoding="utf-8"
    )
    return d


GOOD_BODY = ("# 标题\n\n" + "这是一段足够长的正文内容，用来通过正文长度校验。\n" * 10)


class ParseFrontmatterTest(unittest.TestCase):
    def test_parses_simple_fields(self):
        fields, body = validate.parse_frontmatter(
            "---\nname: demo\ndescription: 测试用\n---\n\n正文"
        )
        self.assertEqual(fields, {"name": "demo", "description": "测试用"})
        self.assertEqual(body.strip(), "正文")

    def test_missing_opening_marker(self):
        with self.assertRaises(ValueError):
            validate.parse_frontmatter("name: demo\n")

    def test_unclosed_frontmatter(self):
        with self.assertRaises(ValueError):
            validate.parse_frontmatter("---\nname: demo\n")

    def test_nested_field_rejected(self):
        with self.assertRaises(ValueError):
            validate.parse_frontmatter("---\nname: demo\n  sub: x\n---\n")

    def test_value_quotes_stripped(self):
        fields, _ = validate.parse_frontmatter(
            "---\nname: 'demo'\ndescription: \"测试\"\n---\n"
        )
        self.assertEqual(fields["name"], "demo")
        self.assertEqual(fields["description"], "测试")


class ValidateSkillTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.tmp_path = Path(self.tmp.name)

    def good_frontmatter(self, name="demo-skill"):
        return (
            f"name: {name}\n"
            "description: 一个用于测试的合规 skill，描述信息完整且具体。\n"
        )

    def test_valid_skill_passes(self):
        d = make_skill(self.tmp_path, "demo-skill", self.good_frontmatter(), GOOD_BODY)
        self.assertEqual(validate.validate_skill(d), [])

    def test_missing_skill_md(self):
        d = self.tmp_path / "empty"
        d.mkdir()
        problems = validate.validate_skill(d)
        self.assertTrue(any("缺少 SKILL.md" in p for p in problems))

    def test_missing_description(self):
        fm = "name: demo-skill\n"
        d = make_skill(self.tmp_path, "demo-skill", fm, GOOD_BODY)
        problems = validate.validate_skill(d)
        self.assertTrue(any("缺少 description" in p for p in problems))

    def test_name_mismatch_with_dir(self):
        d = make_skill(self.tmp_path, "real-name", self.good_frontmatter("other"), GOOD_BODY)
        problems = validate.validate_skill(d)
        self.assertTrue(any("与目录名不一致" in p for p in problems))

    def test_invalid_name_characters(self):
        d = make_skill(self.tmp_path, "Bad_Name", "name: Bad_Name\ndescription: x\n", GOOD_BODY)
        problems = validate.validate_skill(d)
        self.assertTrue(any("不合规" in p for p in problems))

    def test_name_too_long(self):
        long_name = "a" * 65
        d = make_skill(self.tmp_path, long_name, f"name: {long_name}\ndescription: x\n", GOOD_BODY)
        problems = validate.validate_skill(d)
        self.assertTrue(any("不合规" in p for p in problems))

    def test_description_too_long(self):
        fm = "name: demo-skill\ndescription: " + "长" * 1025 + "\n"
        d = make_skill(self.tmp_path, "demo-skill", fm, GOOD_BODY)
        problems = validate.validate_skill(d)
        self.assertTrue(any("超过上限" in p for p in problems))

    def test_body_too_short(self):
        d = make_skill(self.tmp_path, "demo-skill", self.good_frontmatter(), "太短")
        problems = validate.validate_skill(d)
        self.assertTrue(any("正文过短" in p for p in problems))

    def test_placeholder_word_rejected(self):
        body = GOOD_BODY + "\nTODO: 之后补充章节\n"
        d = make_skill(self.tmp_path, "demo-skill", self.good_frontmatter(), body)
        problems = validate.validate_skill(d)
        self.assertTrue(any("TODO" in p for p in problems))

    def test_extension_fields_reported(self):
        fm = self.good_frontmatter() + "allowed-tools: a, b\n"
        d = make_skill(self.tmp_path, "demo-skill", fm, GOOD_BODY)
        problems = validate.validate_skill(d)
        self.assertTrue(any("扩展字段" in p for p in problems))


class DiscoverTest(unittest.TestCase):
    def test_discover_from_parent_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_skill(root, "a", "name: a\ndescription: x\n", GOOD_BODY)
            make_skill(root, "b", "name: b\ndescription: x\n", GOOD_BODY)
            (root / "not-a-skill").mkdir()
            found = validate.discover_skill_dirs([root])
            self.assertEqual([d.name for d in found], ["a", "b"])

    def test_discover_single_skill_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = make_skill(Path(tmp), "solo", "name: solo\ndescription: x\n", GOOD_BODY)
            self.assertEqual([x.name for x in validate.discover_skill_dirs([d])], ["solo"])


class RealSkillsTest(unittest.TestCase):
    """仓库自带的 skills 必须全部通过校验。"""

    def test_bundled_skills_pass(self):
        problems: list[str] = []
        for d in validate.discover_skill_dirs():
            problems.extend(validate.validate_skill(d))
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
