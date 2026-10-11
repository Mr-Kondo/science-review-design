"""配布ファイルと評価データの契約を検査。判断の正確さや起動率は検査しない。"""

import ast
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_entrypoint_and_references(self):
        body = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertLess(len(body.splitlines()), 500)
        header = body.split("---\n", 2)[1].splitlines()
        fields = dict(line.split(": ", 1) for line in header if ": " in line and not line.startswith(" "))
        self.assertEqual(fields["name"], ROOT.name)
        self.assertGreater(len(fields["description"]), 0)
        self.assertLessEqual(len(fields["description"]), 1024)
        self.assertEqual(set(fields), {"name", "description"})
        links = re.findall(r"\]\(([^)]+)\)", body)
        self.assertTrue(links)
        for link in links:
            with self.subTest(link=link):
                path = ROOT / link
                self.assertTrue(path.exists())
                self.assertTrue(path.resolve().is_relative_to(ROOT.resolve()))

    def test_review_cases_and_fixtures(self):
        data = json.loads((ROOT / "evals/cases.json").read_text(encoding="utf-8"))
        cases = data["cases"]
        self.assertTrue(data["frozen_before_model_execution"])
        self.assertGreaterEqual(len(cases), 20)
        self.assertEqual(len({case["id"] for case in cases}), len(cases))
        self.assertGreaterEqual(sum(case["mode"] == "相談" for case in cases), 4)
        used = set()
        for case in cases:
            with self.subTest(case=case["id"]):
                for field in ("prompt", "expected_judgment", "forbidden_behavior"):
                    self.assertTrue(case[field])
                self.assertTrue(case["scoring"]["criteria"])
                for fixture in case["fixtures"]:
                    path = (ROOT / "evals" / fixture).resolve()
                    self.assertTrue(path.is_relative_to((ROOT / "evals/fixtures").resolve()))
                    self.assertTrue(path.is_file())
                    used.add(path)
        self.assertEqual(used, {path.resolve() for path in (ROOT / "evals/fixtures").rglob("*") if path.is_file()})
        for path in used:
            if path.suffix == ".json":
                json.loads(path.read_text(encoding="utf-8"))

    def test_trigger_balance(self):
        cases = json.loads((ROOT / "evals/trigger-cases.json").read_text(encoding="utf-8"))["cases"]
        self.assertEqual(len(cases), 20)
        self.assertEqual(len({case["id"] for case in cases}), 20)
        self.assertEqual(sum(case["expected_trigger"] is True for case in cases), 10)
        self.assertEqual(sum(case["expected_trigger"] is False for case in cases), 10)
        self.assertTrue(all(case["prompt"] and case["reason"] for case in cases))

    def test_no_project_specific_dependency(self):
        prohibited = re.compile(r"Defy|Project_Defy|天稟|アル|P[0-9]-[PCS]-|P0[〜～]P9|第[0-9０-９]+形態")
        for path in ROOT.rglob("*"):
            if {"model-runs", "probe-logs", "extended-raw"}.intersection(path.relative_to(ROOT).parts):
                continue
            if path.suffix in (".md", ".json", ".py") and path.is_file():
                if path.name in ("design-sources.md", "verification-results.md", "test_package.py"):
                    continue
                with self.subTest(path=str(path.relative_to(ROOT))):
                    self.assertIsNone(prohibited.search(path.read_text(encoding="utf-8")))

    def test_parser_has_no_execution_or_external_dependency(self):
        tree = ast.parse((ROOT / "scripts/dimcheck.py").read_text(encoding="utf-8"))
        imports = {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        imports |= {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        self.assertLessEqual(imports, {"ast", "dataclasses", "decimal", "math", "re", "sys"})
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, {"eval", "exec", "compile"})


if __name__ == "__main__":
    unittest.main()
