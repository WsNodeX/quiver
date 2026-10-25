"""install.py 的单元测试。"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

_spec = importlib.util.spec_from_file_location("quiver_install", SCRIPTS / "install.py")
install = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(install)


class InstallTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.tmp_path = Path(self.tmp.name)
        self.target = self.tmp_path / "target"

    def test_install_one_copies_directory(self):
        ok = install.install_one("jd-decoder", self.target, force=False)
        self.assertTrue(ok)
        copied = self.target / "jd-decoder" / "SKILL.md"
        self.assertTrue(copied.is_file())
        self.assertIn("name: jd-decoder", copied.read_text(encoding="utf-8"))

    def test_install_unknown_skill_skips(self):
        ok = install.install_one("no-such-skill", self.target, force=False)
        self.assertFalse(ok)
        self.assertFalse(self.target.exists())

    def test_existing_target_skips_without_force(self):
        dest = self.target / "jd-decoder"
        dest.mkdir(parents=True)
        marker = dest / "marker.txt"
        marker.write_text("keep", encoding="utf-8")
        ok = install.install_one("jd-decoder", self.target, force=False)
        self.assertFalse(ok)
        self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_force_overwrites_existing_target(self):
        dest = self.target / "jd-decoder"
        dest.mkdir(parents=True)
        (dest / "marker.txt").write_text("old", encoding="utf-8")
        ok = install.install_one("jd-decoder", self.target, force=True)
        self.assertTrue(ok)
        self.assertFalse((dest / "marker.txt").exists())
        self.assertTrue((dest / "SKILL.md").is_file())

    def test_available_skills_include_bundled(self):
        names = install.available_skills()
        for expected in ("jd-decoder", "interview-grill", "resume-reviewer", "readme-booster"):
            self.assertIn(expected, names)

    def test_cli_all_installs_everything(self):
        rc = install.main(["install.py", "--all", "--target", str(self.target)])
        self.assertEqual(rc, 0)
        for name in install.available_skills():
            self.assertTrue((self.target / name / "SKILL.md").is_file())

    def test_cli_single_skill(self):
        rc = install.main(
            ["install.py", "resume-reviewer", "--target", str(self.target)]
        )
        self.assertEqual(rc, 0)
        self.assertTrue((self.target / "resume-reviewer" / "SKILL.md").is_file())

    def test_cli_no_args_fails(self):
        self.assertEqual(install.main(["install.py", "--target", str(self.target)]), 2)


if __name__ == "__main__":
    unittest.main()
