"""CLIの終了コード・数値・誤換算・入力境界を検査する。モデル監修の評価ではない。"""

from pathlib import Path
import math
import os
import subprocess
import sys
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "dimcheck.py"


class DimcheckTests(unittest.TestCase):
    def run_cli(self, *args):
        result = subprocess.run([sys.executable, str(SCRIPT), *args],
                                capture_output=True, encoding="utf-8", timeout=5,
                                env={**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"})
        self.assertNotIn("Traceback", result.stderr)
        return result

    def test_dimension_cases(self):
        cases = [
            (("eq", "J", "kg*m²/s²"), 0),
            (("eq", "J", "kg*m/s"), 1),
            (("same", "Gy", "J/kg"), 0),
            (("same", "Hz", "Bq"), 0),
            (("same", "N*m", "J"), 0),
            (("dim", "m*s⁻²"), 0),
            (("eq", "Wh", "W*h"), 0),
            (("eq", "Pa", "N/m^2"), 0),
            (("eq", "V", "W/A"), 0),
            (("eq", "J", "0.5*kg*(m/s)^2"), 0),
            (("dim", "0*m"), 0),
        ]
        for args, status in cases:
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual(result.returncode, status, result.stderr)
                self.assertIn("次元", result.stdout)
                if args[0] in ("same", "eq"):
                    self.assertIn("別に確認", result.stdout)

    def test_conversion_values(self):
        cases = [
            ("36", "km/h", "m/s", 10.0),
            ("1", "Gy", "mGy", 1000.0),
            ("1", "Hz", "kHz", 0.001),
            ("2.5", "kWh", "J", 9e6),
            ("1", "L", "m^3", 0.001),
            ("14.05", "MeV", "J", 14.05e6 * 1.602176634e-19),
            ("1", "J", "N*m", 1.0),
            ("2", "mm", "m", 0.002),
            ("1", "um", "μm", 1.0),
            ("1", "kOhm", "Ω", 1000.0),
            ("1", "dam", "m", 10.0),
            ("0", "m", "km", 0.0),
            ("-2", "m", "cm", -200.0),
        ]
        for value, source, target, expected in cases:
            with self.subTest(source=source, target=target):
                result = self.run_cli("conv", value, source, target)
                self.assertEqual(result.returncode, 0, result.stderr)
                actual = float(result.stdout.split()[0])
                self.assertTrue(math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-100))
                if source == "J" and target == "N*m":
                    self.assertIn("トルクか仕事かは式の意味", result.stdout)

    def test_semantic_conversion_rejected(self):
        for source, target in [("Gy", "Sv"), ("Sv", "Gy"), ("Hz", "Bq"), ("Bq", "Hz"),
                               ("mGy", "mSv"), ("kHz", "kBq"), ("Gy", "J/kg"),
                               ("Gy/Gy", "Sv/Sv"), ("Gy*Sv", "Gy*Sv")]:
            with self.subTest(source=source, target=target):
                result = self.run_cli("conv", "1", source, target)
                self.assertEqual(result.returncode, 2)
                self.assertIn("意味", result.stderr)

    def test_bad_expressions(self):
        cases = ["", " ", "unknown", "(", "m^", "m/0", "0^-1", "m//s", "m+s",
                 "m^0.5", "m^(2*2)", "m^33", "1e101*m", "1e-101*m", "nan", "Infinity",
                 "1e999", "1e-999", "1e100*1e100", "1e-100*1e-100", "(1e-100)^32",
                 "1e100/1e-100", "m" * 2049, "(" * 25 + "m" + ")" * 25,
                 "*".join(["m"] * 50), "((m^32)^32)", "m m", "__import__('os')",
                 "m.__class__", "f(m)", "[m]", "m[0]", "True", "1j", "0x10*m", "m;ls",
                 "℃", "degF", "m/s)", "m**", "m^^2", "1_000*m"]
        for expression in cases:
            with self.subTest(expression=expression):
                result = self.run_cli("dim", expression)
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertIn("入力エラー", result.stderr)

    def test_bad_conversion_input_and_results(self):
        for args in [("nan", "m", "m"), ("inf", "m", "m"), ("-Infinity", "m", "m"),
                     ("1e101", "m", "m"), ("1e-999", "m", "m"), ("1", "0*m", "m"),
                     ("1", "m", "0*m"), ("1", "-1*m", "m"), ("1", "℃", "K"),
                     ("1", "1e100*m", "1e-100*m"), ("1e100", "km", "m"),
                     ("1e-100", "mm", "m")]:
            with self.subTest(args=args):
                result = self.run_cli("conv", *args)
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertIn("入力エラー", result.stderr)
        self.assertEqual(self.run_cli("conv", "1", "m", "s").returncode, 1)

    def test_limits_and_help(self):
        for expression in ["m^32", "(" * 24 + "m" + ")" * 24, "1e100", "1e-100"]:
            with self.subTest(expression=expression):
                self.assertEqual(self.run_cli("dim", expression).returncode, 0)
        self.assertEqual(self.run_cli("--help").returncode, 0)
        for args in [(), ("bad",), ("dim",), ("same", "m"), ("conv", "1", "m")]:
            with self.subTest(args=args):
                self.assertEqual(self.run_cli(*args).returncode, 2)


if __name__ == "__main__":
    unittest.main()
