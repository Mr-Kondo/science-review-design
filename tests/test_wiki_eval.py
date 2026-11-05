"""Meaningful trial invariants; no model/network calls in tests."""
import json
import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import wiki_eval as w


class TrialTests(unittest.TestCase):
    def plan(self, phase="quality"):
        return {"phase": phase, "axes": w.AXES[phase],
                "tasks": w.tasks(phase, [{"id": "Q1", "prompt": "input", "expected": "SECRET"}],
                                 {"current": "a", "candidate": "b"})}

    def scores(self, plan):
        return {"scores": [{"id": t["id"], "axes": {a: True for a in plan["axes"]},
                            "evidence": "observed calculation and verdict"} for t in plan["tasks"]]}

    def test_no_answer_leak_and_counterbalanced_order(self):
        tasks = self.plan()["tasks"]
        self.assertNotIn("SECRET", json.dumps(tasks))
        self.assertEqual([t["condition"] for t in tasks], ["current", "candidate", "candidate", "current"])

    def test_ties_hold_and_replicated_improvement_supports(self):
        plan = self.plan()
        scores = self.scores(plan)
        self.assertEqual(w.summarize(plan, scores)["decision"], "hold")
        for row in scores["scores"]:
            if row["id"].endswith("current"):
                row["axes"]["consistent"] = False
        self.assertEqual(w.summarize(plan, scores)["decision"], "provisional_support")
        scores["scores"][2]["axes"]["science"] = False
        self.assertEqual(w.summarize(plan, scores)["decision"], "hold")

    def test_partial_duplicate_or_unsubstantiated_scores_refused(self):
        plan = self.plan()
        for mutate in (lambda x: x["scores"].pop(),
                       lambda x: x["scores"].__setitem__(0, x["scores"][1]),
                       lambda x: x["scores"][0].__setitem__("evidence", ""),
                       lambda x: x["scores"][0]["axes"].__setitem__("science", 1)):
            scores = self.scores(plan)
            mutate(scores)
            with self.assertRaises(ValueError):
                w.summarize(plan, scores)

    def test_frozen_plan_integrity_and_output_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            raw = w.encode(self.plan())
            w.create(path / "plan.json", raw)
            w.create(path / "plan.sha256", w.digest(raw).encode())
            self.assertEqual(w.load_plan(path)["phase"], "quality")
            with self.assertRaises(FileExistsError):
                w.create(path / "plan.json", b"replace")
            (path / "plan.json").write_bytes(raw + b" ")
            with self.assertRaises(ValueError):
                w.load_plan(path)

    def test_timeout_and_malformed_output_saved_without_retry(self):
        outputs = (subprocess.TimeoutExpired("claude", 1, output=b"partial", stderr=b"timeout"),
                   subprocess.CompletedProcess([], 0, stdout=b"not-json", stderr=b""))
        for output in outputs:
            with tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary)
                kwargs = {"side_effect": output} if isinstance(output, Exception) else {"return_value": output}
                with patch.object(subprocess, "run", **kwargs) as call:
                    with self.assertRaises(RuntimeError):
                        w.call(path, "trial", "system", "input", 1)
                    self.assertEqual(call.call_count, 1)
                    self.assertTrue((path / "trial.stdout.json").exists())
                    self.assertFalse(json.loads((path / "trial.meta.json").read_text())["ok"])
                    with self.assertRaises(FileExistsError):
                        w.call(path, "trial", "system", "input", 1)
                    self.assertEqual(call.call_count, 1)

    def test_wrong_model_is_not_comparable(self):
        raw = w.encode({"result": "answer", "modelUsage": {"other-model": {}}})
        with tempfile.TemporaryDirectory() as temporary, patch.object(
                subprocess, "run", return_value=subprocess.CompletedProcess([], 0, raw, b"")):
            with self.assertRaises(RuntimeError):
                w.call(Path(temporary), "wrong", "system", "input")

    def test_launch_error_saved_and_success_uses_isolation(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            with patch.object(subprocess, "run", side_effect=OSError("launch failed")):
                with self.assertRaises(RuntimeError):
                    w.call(path, "failure", "system", "input")
            self.assertEqual(json.loads((path / "failure.meta.json").read_text(encoding="utf-8"))["error"], "launch_error")
            raw = w.encode({"result": "answer", "modelUsage": {"claude-sonnet-5-5": {}}, "total_cost_usd": 0.1})
            with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 0, raw, b"")) as call:
                result = w.call(path, "success", "system", "input")
                self.assertTrue(result["ok"])
                args = call.call_args
                self.assertNotEqual(Path(args.kwargs["cwd"]), path)
                self.assertFalse(Path(args.kwargs["cwd"]).exists())
                self.assertIn("--safe-mode", args.args[0])
                position = args.args[0].index("--setting-sources")
                self.assertEqual(args.args[0][position + 1], "user")

    def test_inconsistent_cases_across_repeats_do_not_support(self):
        plan = self.plan()
        plan["tasks"] = w.tasks("quality", [{"id": "Q1", "prompt": "a"}, {"id": "Q2", "prompt": "b"}],
                                {"current": "a", "candidate": "b"})
        scores = self.scores(plan)
        for row in scores["scores"]:
            if row["id"] in ("Q1-r1-current", "Q2-r2-current"):
                row["axes"]["consistent"] = False
        self.assertEqual(w.summarize(plan, scores)["decision"], "hold")

    def test_maintenance_scoring_and_invalid_shapes(self):
        plan = self.plan("maintenance")
        scores = self.scores(plan)
        self.assertEqual(w.summarize(plan, scores)["decision"], "hold")
        scores["scores"][0]["axes"]["evidence"] = False
        self.assertEqual(w.summarize(plan, scores)["decision"], "provisional_support")
        for invalid in (None, {}, {"scores": [None]}, {"scores": [{"id": "x"}]}):
            with self.assertRaises(ValueError):
                w.summarize(plan, invalid)

    def test_freeze_counts_candidate_chain_and_single_batch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "feedback").mkdir()
            (root / "tools").mkdir()
            (root / "tools/wiki-cases.json").write_bytes((w.ROOT / "tools/wiki-cases.json").read_bytes())
            for name in ("adr/delivery-and-output-contracts.md",
                         "evals/science-review/verification-results.md",
                         "knowledge/index.md", "knowledge/verdict-consistency.md", "knowledge/unsupported-performance.md"):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("synthetic evidence", encoding="utf-8")
            skill = root / "skill.md"
            skill.write_bytes(b"base\r\n")
            for case in ("ST02", "ST03"):
                target = root / f"feedback/issue-1/{case}-after-final.stdout.json"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(w.encode({"result": "synthetic output"}))
            with patch.object(w, "ROOT", root), patch.object(w, "SKILL", skill), \
                    patch.object(w, "cli_version", return_value="fixed"):
                maintenance = root / "feedback/maintenance"
                self.assertEqual(w.freeze("maintenance", maintenance)["tasks"], 8)
                plan = w.load_plan(maintenance)
                self.assertEqual(plan["sources"]["SKILL.md"], w.digest(b"base\r\n"))
                self.assertEqual(len(plan["rubric"]), 4)
                with self.assertRaises(ValueError):
                    w.trial_path(root / "outside")
                with self.assertRaises(ValueError):
                    w.freeze("quality", root / "feedback/no-candidate")
                candidate = root / "candidate.md"
                candidate.write_text("changed", encoding="utf-8")
                with self.assertRaises(ValueError):
                    w.freeze("quality", root / "feedback/no-selection", candidate)
                selection = root / "selection.json"
                (maintenance / "summary.json").write_bytes(b"{}")
                selection.write_bytes(w.encode({"maintenance_directory": str(maintenance),
                    "reason": "one local change", "target_axis": "consistent",
                    "candidate_sha256": w.digest(candidate.read_bytes()),
                    "maintenance_summary_sha256": w.digest(b"{}")}))
                with self.assertRaises(ValueError):
                    w.freeze("quality", root / "feedback/incomplete", candidate, selection)
                (maintenance / "run.complete").write_bytes(b"complete")
                quality = root / "feedback/quality"
                self.assertEqual(w.freeze("quality", quality, candidate, selection)["tasks"], 16)
                self.assertTrue(w.load_plan(quality)["candidate_diff"])
                with patch.object(w, "call", side_effect=RuntimeError("first failure")) as call:
                    with self.assertRaises(RuntimeError):
                        w.run(quality)
                    self.assertEqual(call.call_count, 1)
                    with self.assertRaises(FileExistsError):
                        w.run(quality)
                    self.assertEqual(call.call_count, 1)


if __name__ == "__main__":
    unittest.main()
