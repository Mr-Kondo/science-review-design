#!/usr/bin/env python3
"""単位式の次元検査・尺度換算（Python 3.10以上、標準ライブラリのみ）。

dim EXPR / same EXPR EXPR / eq EXPR EXPR / conv VALUE FROM TO
例: eq J 'kg*m²/s²' / conv 36 km/h m/s
構文: 単位名、有限数の係数、* /、括弧、整数指数（^ または **）。
終了: 0=成功、1=次元不一致、2=入力エラー・未対応・意味の確認が必要。
same/eqの成功は次元一致だけ。係数・量の意味・モデルの正しさは保証しない。
Gy/Sv・Hz/Bqの異なる意味、またはその意味が失われた式のconvは拒否する。
JとN*mの尺度対応は、トルクか仕事かを決めない。℃/℉のオフセットは未対応。
限界: 式2048文字、AST128ノード、括弧・演算深さ24、指数絶対値32、
各次元指数絶対値128。非ゼロの数値・尺度・結果の絶対値は1e-100〜1e100。
登録: SI基本・代表的組立、SI接頭辞、g/t/min/h/L/Wh/eV、Gy/Sv/Bq/Hz。
"""

import ast
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import math
import re
import sys


BASE = ("kg", "m", "s", "A", "K", "mol", "cd")
MAX_LENGTH, MAX_NODES, MAX_DEPTH, MAX_EXPONENT = 2048, 128, 24, 32
MIN_VALUE, MAX_VALUE = 1e-100, 1e100
NUMBER = r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
TOKEN = re.compile(rf"{NUMBER}|[A-Za-z]+|[*/^()+-]")


class InputError(ValueError):
    pass


@dataclass(frozen=True)
class Unit:
    scale: float
    dims: tuple[int, ...]
    meanings: frozenset[str] = frozenset()


def unit(scale=1.0, meaning="", **powers):
    return Unit(scale, tuple(powers.get(name, 0) for name in BASE),
                frozenset([meaning]) if meaning else frozenset())


UNITS = {
    "kg": unit(kg=1), "g": unit(1e-3, kg=1), "t": unit(1e3, kg=1),
    "m": unit(m=1), "s": unit(s=1), "A": unit(A=1), "K": unit(K=1),
    "mol": unit(mol=1), "cd": unit(cd=1), "rad": unit(), "sr": unit(),
    "min": unit(60, s=1), "h": unit(3600, s=1), "L": unit(1e-3, m=3),
    "N": unit(kg=1, m=1, s=-2), "J": unit(kg=1, m=2, s=-2),
    "W": unit(kg=1, m=2, s=-3), "Pa": unit(kg=1, m=-1, s=-2),
    "C": unit(A=1, s=1), "V": unit(kg=1, m=2, s=-3, A=-1),
    "F": unit(kg=-1, m=-2, s=4, A=2), "Ohm": unit(kg=1, m=2, s=-3, A=-2),
    "S": unit(kg=-1, m=-2, s=3, A=2), "Wb": unit(kg=1, m=2, s=-2, A=-1),
    "T": unit(kg=1, s=-2, A=-1), "H": unit(kg=1, m=2, s=-2, A=-2),
    "lm": unit(cd=1), "lx": unit(cd=1, m=-2), "kat": unit(mol=1, s=-1),
    "Wh": unit(3600, kg=1, m=2, s=-2), "eV": unit(1.602176634e-19, kg=1, m=2, s=-2),
    "Gy": unit(meaning="吸収線量", m=2, s=-2),
    "Sv": unit(meaning="線量当量等", m=2, s=-2),
    "Hz": unit(meaning="周波数", s=-1), "Bq": unit(meaning="放射能", s=-1),
}
PREFIXES = dict(zip(
    ("Q", "R", "Y", "Z", "E", "P", "T", "G", "M", "k", "h", "da",
     "d", "c", "m", "u", "n", "p", "f", "a", "z", "y", "r", "q"),
    (10.0 ** n for n in (30, 27, 24, 21, 18, 15, 12, 9, 6, 3, 2, 1,
                         -1, -2, -3, -6, -9, -12, -15, -18, -21, -24, -27, -30))))
PREFIXABLE = set(UNITS) - {"kg", "t", "min", "h"}


def bounded(value):
    if not math.isfinite(value) or (value != 0 and not MIN_VALUE <= abs(value) <= MAX_VALUE):
        raise InputError("非有限または数値上限・下限を超えています（非ゼロは1e-100〜1e100）")
    return value


def scalar(text):
    if len(text) > MAX_LENGTH or not re.fullmatch(rf"[+-]?{NUMBER}", text):
        raise InputError("数値は有限の十進数で指定してください")
    number = Decimal(text)
    if number and not Decimal("1e-100") <= abs(number) <= Decimal("1e100"):
        raise InputError("数値上限・下限を超えています（非ゼロは1e-100〜1e100）")
    return bounded(float(number))


def named_unit(name):
    if name in UNITS:
        return UNITS[name]
    for prefix in sorted(PREFIXES, key=len, reverse=True):
        base = name[len(prefix):]
        if name.startswith(prefix) and base in PREFIXABLE:
            source = UNITS[base]
            return Unit(bounded(source.scale * PREFIXES[prefix]), source.dims, source.meanings)
    raise InputError(f"未知または未対応の単位: {name}")


def parse(text):
    if not text.strip() or len(text) > MAX_LENGTH:
        raise InputError("空の式または2048文字を超える式です")
    if any(mark in text for mark in ("℃", "℉", "°", "degC", "degF")):
        raise InputError("オフセット温度の換算は未対応です")
    for old, new in (("⁻¹", "^-1"), ("⁻²", "^-2"), ("²", "^2"), ("³", "^3"),
                     ("·", "*"), ("⋅", "*"), ("×", "*"), ("µ", "u"), ("μ", "u"), ("Ω", "Ohm")):
        text = text.replace(old, new)
    if len(text) > MAX_LENGTH:
        raise InputError("正規化後の式が2048文字を超えています")
    depth, pos = 0, 0
    for match in TOKEN.finditer(text):
        if text[pos:match.start()].strip():
            raise InputError("単位名・数値・乗除・括弧・整数指数だけに対応します")
        token = match.group()
        if re.fullmatch(NUMBER, token):
            scalar(token)
        if token == "(":
            depth += 1
            if depth > MAX_DEPTH:
                raise InputError("括弧の深さが24を超えています")
        elif token == ")":
            depth -= 1
            if depth < 0:
                raise InputError("括弧の対応が不正です")
        pos = match.end()
    if text[pos:].strip() or depth:
        raise InputError("未対応の文字または閉じていない括弧です")
    expression = text.strip().replace("^", "**")
    try:
        tree = ast.parse(expression, mode="eval")
    except (SyntaxError, ValueError) as error:
        raise InputError("式の構文が不正です。指数・演算子・括弧を確認してください") from error
    if sum(1 for _ in ast.walk(tree)) > MAX_NODES:
        raise InputError("式が128ノードを超えています")
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            scalar(ast.get_source_segment(expression, node))

    def integer(node):
        if isinstance(node, ast.Constant) and type(node.value) is int:
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            if isinstance(node.operand, ast.Constant) and type(node.operand.value) is int:
                return node.operand.value * (-1 if isinstance(node.op, ast.USub) else 1)
        raise InputError("指数は整数定数のみ対応します")

    def visit(node, level=0):
        if level > MAX_DEPTH:
            raise InputError("演算の深さが24を超えています")
        if isinstance(node, ast.Name):
            return named_unit(node.id)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return unit(bounded(float(node.value)))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            if isinstance(node.operand, ast.Constant) and type(node.operand.value) in (int, float):
                return unit(bounded(float(node.operand.value) * (-1 if isinstance(node.op, ast.USub) else 1)))
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Mult, ast.Div, ast.Pow)):
            left = visit(node.left, level + 1)
            if isinstance(node.op, ast.Pow):
                exponent = integer(node.right)
                if abs(exponent) > MAX_EXPONENT:
                    raise InputError("指数の絶対値が32を超えています")
                scale = bounded(left.scale ** exponent)
                dims = tuple(power * exponent for power in left.dims)
                meanings = left.meanings
            else:
                right = visit(node.right, level + 1)
                division = isinstance(node.op, ast.Div)
                scale = bounded(left.scale / right.scale if division else left.scale * right.scale)
                if scale == 0 and left.scale != 0 and right.scale != 0:
                    raise InputError("演算結果がアンダーフローしました")
                dims = tuple(a - b if division else a + b for a, b in zip(left.dims, right.dims))
                meanings = left.meanings | right.meanings
            if abs(max(dims, key=abs)) > 128:
                raise InputError("次元指数の絶対値が128を超えています")
            if scale == 0 and left.scale != 0 and isinstance(node.op, ast.Pow):
                raise InputError("演算結果がアンダーフローしました")
            return Unit(scale, dims, meanings)
        raise InputError("式には乗除と整数指数だけを使ってください")

    return visit(tree.body)


def fmt(dims):
    return "[" + (" ".join(f"{name}^{power}" for name, power in zip(BASE, dims) if power) or "無次元") + "]"


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if args in (["--help"], ["-h"]):
        print(__doc__)
        return 0
    try:
        if len(args) == 2 and args[0] == "dim":
            value = parse(args[1])
            print(f"次元 {fmt(value.dims)}; SI尺度 {value.scale:.12g}; 明示された意味 {', '.join(sorted(value.meanings)) or '未指定'}")
            print("次元だけでは量の意味・係数・モデルは確認できません。")
            return 0
        if len(args) == 3 and args[0] in ("same", "eq"):
            left, right = parse(args[1]), parse(args[2])
            same = left.dims == right.dims
            print(f"次元{'一致' if same else '不一致'}: {fmt(left.dims)} / {fmt(right.dims)}")
            print("量の同一性・等式の係数・物理モデルの正しさは別に確認してください。")
            return 0 if same else 1
        if len(args) == 4 and args[0] == "conv":
            number, left, right = scalar(args[1]), parse(args[2]), parse(args[3])
            if left.dims != right.dims:
                print(f"次元不一致: {fmt(left.dims)} / {fmt(right.dims)}")
                return 1
            if left.scale <= 0 or right.scale <= 0:
                raise InputError("換算元・換算先の尺度は正の数である必要があります")
            # shortcut: 明示された意味だけを保守的に追跡。完全な量の意味論が必要なら監修へ戻す。
            if left.meanings != right.meanings or len(left.meanings) > 1:
                raise InputError("量の意味が異なるか不明です。Gy/Sv・Hz/Bq等の換算には意味と条件の確認が必要です")
            ratio = bounded(left.scale / right.scale)
            if ratio == 0:
                raise InputError("換算比がアンダーフローしました")
            result = bounded(number * ratio)
            if result == 0 and number != 0:
                raise InputError("換算結果がアンダーフローしました")
            print(f"{result:.12g} {args[3]} （尺度換算）")
            print("量の意味は式の文脈で確認してください。トルクか仕事かは式の意味によります。")
            return 0
        raise InputError("使い方: dim EXPR / same EXPR EXPR / eq EXPR EXPR / conv VALUE FROM TO（--help）")
    except (InputError, OverflowError, ZeroDivisionError, InvalidOperation, RecursionError) as error:
        detail = "ゼロ除算またはゼロの負指数です" if isinstance(error, ZeroDivisionError) else str(error)
        if isinstance(error, OverflowError):
            detail = "演算結果が数値上限を超えています"
        print(f"入力エラー: {detail}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
