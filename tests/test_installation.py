"""Exercise installation, update, deletion, and refusal paths in temporary projects."""

import contextlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import install
import uninstall


class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name).resolve() / "日本語 project"
        self.project.mkdir()
        self.args = ["--scope", "project", "--project-dir", str(self.project)]
        self.codex = self.project / ".agents/skills/science-review"
        self.claude = self.project / ".claude/skills/science-review"

    def call(self, main, extra=()):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return main([*self.args, *extra])

    def test_install_update_and_remove(self):
        self.assertEqual(self.call(install.main), 0)
        expected = {path.relative_to(install.SOURCE).as_posix(): path.read_bytes()
                    for path in install.package_files()}
        for destination in (self.codex, self.claude):
            actual = {name: (destination / name).read_bytes() for name in install.inventory(destination)
                      if not name.endswith("/")}
            self.assertEqual(actual, expected)
            self.assertFalse((destination / "evals/model-runs").exists())
            self.assertFalse((destination / "evals/model-probe.json").exists())
        source = Path(self.temporary.name).resolve() / "updated-source"
        source.mkdir()
        for path in install.package_files():
            target = source / path.relative_to(install.SOURCE)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        (source / "SKILL.md").write_bytes(b"updated skill\n")
        (source / "references/idea-advice.md").unlink()
        with patch.object(install, "SOURCE", source):
            self.assertEqual(self.call(install.main), 0)
        for destination in (self.codex, self.claude):
            self.assertEqual((destination / "SKILL.md").read_bytes(), b"updated skill\n")
            self.assertFalse((destination / "references/idea-advice.md").exists())
        neighbour = self.codex.parent / "another-skill"
        neighbour.mkdir()
        (neighbour / "keep.txt").write_text("keep")
        self.assertEqual(self.call(uninstall.main), 0)
        self.assertEqual(self.call(uninstall.main), 0)
        self.assertFalse(self.codex.exists())
        self.assertFalse(self.claude.exists())
        self.assertEqual((neighbour / "keep.txt").read_text(), "keep")

    def test_dry_run_does_not_write_or_delete(self):
        self.assertEqual(self.call(install.main, ["--dry-run"]), 0)
        self.assertEqual(list(self.project.iterdir()), [])
        self.assertEqual(self.call(install.main), 0)
        before = install.inventory(self.codex)
        self.assertEqual(self.call(uninstall.main, ["--dry-run"]), 0)
        self.assertEqual(install.inventory(self.codex), before)

    def test_modified_missing_or_extra_entries_refuse_both_targets(self):
        mutations = (
            lambda: (self.claude / "SKILL.md").write_text("my edits"),
            lambda: (self.claude / "scripts/dimcheck.py").unlink(),
            lambda: (self.claude / "personal.txt").write_text("keep"),
            lambda: (self.claude / "empty-notes").mkdir(),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                self.assertEqual(self.call(install.main), 0)
                mutate()
                before = install.inventory(self.claude)
                with patch.object(install, "install_one") as write:
                    self.assertEqual(self.call(install.main), 1)
                    write.assert_not_called()
                self.assertEqual(self.call(uninstall.main), 1)
                self.assertTrue(self.codex.exists())
                self.assertEqual(install.inventory(self.claude), before)
                shutil.rmtree(self.codex)
                shutil.rmtree(self.claude)

    def test_unmanaged_directory_and_invalid_marker_are_preserved(self):
        self.claude.mkdir(parents=True)
        (self.claude / "SKILL.md").write_text("manual copy")
        for marker in (None, "{", "[]", '{"name":"another-skill","schema":1}',
                       '{"name":"science-review","schema":1,"files":{"../keep":"bad"}}'):
            with self.subTest(marker=marker):
                if marker is not None:
                    (self.claude / install.MARKER).write_text(marker)
                self.assertEqual(self.call(install.main), 1)
                self.assertEqual(self.call(uninstall.main), 1)
                self.assertFalse(self.codex.exists())
                self.assertEqual((self.claude / "SKILL.md").read_text(), "manual copy")

    def test_symlinks_in_destination_or_parent_are_refused(self):
        outside = Path(self.temporary.name) / "outside"
        outside.mkdir()
        (outside / "keep").write_text("keep")
        self.codex.parent.mkdir(parents=True)
        try:
            self.codex.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"Symlink creation unavailable: {exc}")
        for main in (install.main, uninstall.main):
            self.assertEqual(self.call(main), 1)
        self.codex.unlink()
        shutil.rmtree(self.project / ".agents")
        (self.project / ".agents").symlink_to(outside, target_is_directory=True)
        self.assertEqual(self.call(install.main), 1)
        self.assertEqual(self.call(uninstall.main), 1)
        self.assertEqual((outside / "keep").read_text(), "keep")
        self.assertFalse(self.claude.exists())

    def test_source_directory_cannot_be_removed_or_overwritten(self):
        with patch.object(install, "SOURCE", self.claude):
            self.claude.mkdir(parents=True)
            with self.assertRaises(ValueError):
                install.check_destination(self.claude)

    def test_failed_replacement_restores_existing_installation(self):
        self.assertEqual(self.call(install.main), 0)
        before = install.inventory(self.codex)
        original = Path.rename

        def fail_new(path, target):
            if path.name == "new":
                raise OSError("simulated replacement failure")
            return original(path, target)

        with patch.object(Path, "rename", fail_new):
            self.assertEqual(self.call(install.main, ["--target", "codex"]), 1)
        self.assertEqual(install.inventory(self.codex), before)
        self.assertTrue(install.check_destination(self.codex))

    def test_generated_python_cache_is_allowed_but_notes_in_cache_are_not(self):
        self.assertEqual(self.call(install.main), 0)
        cache = self.codex / "scripts/__pycache__"
        cache.mkdir()
        (cache / "dimcheck.cpython-314.pyc").write_bytes(b"generated")
        self.assertTrue(install.check_destination(self.codex))
        (cache / "notes.md").write_text("keep")
        self.assertEqual(self.call(uninstall.main), 1)
        (cache / "notes.md").unlink()
        self.assertEqual(self.call(uninstall.main), 0)

    def test_failed_restore_keeps_original_in_temporary_backup(self):
        self.assertEqual(self.call(install.main), 0)
        before = install.inventory(self.codex)
        original = Path.rename

        def fail_new_and_restore(path, target):
            if path.name in ("new", "previous"):
                raise OSError("simulated replacement and restore failure")
            return original(path, target)

        with patch.object(Path, "rename", fail_new_and_restore):
            self.assertEqual(self.call(install.main, ["--target", "codex"]), 1)
        backups = list(self.codex.parent.glob(".science-review-*/previous"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(install.inventory(backups[0]), before)
        self.assertTrue(install.check_destination(backups[0]))

    def test_user_scope_and_single_target(self):
        with patch.object(Path, "home", return_value=self.project):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(install.main(["--target", "codex"]), 0)
                self.assertFalse(self.claude.exists())
                self.assertEqual(uninstall.main(["--target", "codex"]), 0)
        self.assertEqual(self.call(install.main, ["--target", "claude"]), 0)
        self.assertFalse(self.codex.exists())
        self.assertTrue(self.claude.exists())

    def test_invalid_location_does_not_write(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(install.main(["--scope", "project"]), 1)
            self.assertEqual(uninstall.main(["--scope", "user", "--project-dir", str(self.project)]), 1)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_cli_and_installed_skill_work_without_git(self):
        legacy_encoding = {**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"}
        for script, extra in (("install.py", []), ("install.py", []), ("uninstall.py", ["--dry-run"])):
            result = subprocess.run([sys.executable, str(ROOT / "tools" / script), *self.args, *extra],
                                    cwd=self.project, capture_output=True, encoding="utf-8", env=legacy_encoding)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(str(self.project), result.stdout)
        result = subprocess.run([sys.executable, str(self.codex / "scripts/dimcheck.py"),
                                 "conv", "36", "km/h", "m/s"], capture_output=True,
                                encoding="utf-8", env=legacy_encoding)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("10", result.stdout)
        result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(self.codex / "tests")],
                                cwd=self.project, capture_output=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.call(uninstall.main), 0)


if __name__ == "__main__":
    unittest.main()
