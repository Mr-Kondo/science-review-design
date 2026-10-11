#!/usr/bin/env python3
"""単位・次元の検査（標準ライブラリのみ。SymPy 不要）。

目的: 式の両辺の次元が合っているか、単位換算が正しいかを、再現できる形で確かめる。
これは次元の整合を見るだけで、物理モデルの妥当性は保証しない（同じ次元でも別の量がある）。

使い方:
  dimcheck.py dim  "kg*m/s"                 次元ベクトルと、同じ次元を持つ量の候補を表示
  dimcheck.py same "J" "N*m"                次元が一致するか（一致=0 / 不一致=1）
  dimcheck.py eq   "J" "kg*m/s"             左辺=右辺 の次元整合を検査し、不一致なら差を表示
  dimcheck.py conv 2.5 shaku m              数値の単位換算（尺・寸などを含む）

単位式の書き方: * / ^ ( ) が使える。例 "kg*m^2/s^2"、"N*s"、"W*h"、"mm"、"ft/s"、"MeV"。
接頭辞は k M G m u c d n に対応（例: mGy、MeV、mbar）。
登録単位:
  SI 基本・組立 kg g t m s A K mol cd N J W Pa Hz C V F Ohm T、min h L Wh
  放射線        Gy Sv Bq eV   （Gy と Sv は同じ次元だが別の量。単位だけでは区別できない）
  圧力・力      bar atm psi kgf lbf
  ヤード・ポンド in ft lb gr（グレーン）
  その他        cal（= 4.184 J）、尺 shaku（= 10/33 m）、寸 sun（= 尺/10）
終了コード: 0=成功 / 1=次元不一致 / 2=入力エラー。
"""
import re
import sys

BASE = ["kg", "m", "s", "A", "K", "mol", "cd"]


def vec(**kw):
    return tuple(kw.get(b, 0) for b in BASE)


# 名前 -> (SI換算係数, 次元ベクトル)。kg を基準にするため g は 1e-3。
UNITS = {
    "kg": (1.0, vec(kg=1)), "g": (1e-3, vec(kg=1)), "t": (1e3, vec(kg=1)),
    "m": (1.0, vec(m=1)), "s": (1.0, vec(s=1)), "A": (1.0, vec(A=1)),
    "K": (1.0, vec(K=1)), "mol": (1.0, vec(mol=1)), "cd": (1.0, vec(cd=1)),
    "min": (60.0, vec(s=1)), "h": (3600.0, vec(s=1)),
    "L": (1e-3, vec(m=3)),
    "N": (1.0, vec(kg=1, m=1, s=-2)), "J": (1.0, vec(kg=1, m=2, s=-2)),
    "W": (1.0, vec(kg=1, m=2, s=-3)), "Pa": (1.0, vec(kg=1, m=-1, s=-2)),
    "Hz": (1.0, vec(s=-1)), "C": (1.0, vec(A=1, s=1)),
    "V": (1.0, vec(kg=1, m=2, s=-3, A=-1)), "F": (1.0, vec(kg=-1, m=-2, s=4, A=2)),
    "Ohm": (1.0, vec(kg=1, m=2, s=-3, A=-2)), "T": (1.0, vec(kg=1, s=-2, A=-1)),
    "Wh": (3600.0, vec(kg=1, m=2, s=-2)),
    # 放射線（Gy と Sv は次元が同じ J/kg。量の違いは単位から判別できない）
    "Gy": (1.0, vec(m=2, s=-2)), "Sv": (1.0, vec(m=2, s=-2)), "Bq": (1.0, vec(s=-1)),
    "eV": (1.602176634e-19, vec(kg=1, m=2, s=-2)),
    # 圧力・力・熱量
    "bar": (1e5, vec(kg=1, m=-1, s=-2)), "atm": (101325.0, vec(kg=1, m=-1, s=-2)),
    "psi": (6894.757293168, vec(kg=1, m=-1, s=-2)),
    "kgf": (9.80665, vec(kg=1, m=1, s=-2)), "lbf": (4.4482216152605, vec(kg=1, m=1, s=-2)),
    "cal": (4.184, vec(kg=1, m=2, s=-2)),
    # ヤード・ポンド
    "in": (0.0254, vec(m=1)), "ft": (0.3048, vec(m=1)),
    "lb": (0.45359237, vec(kg=1)), "gr": (64.79891e-6, vec(kg=1)),
    "shaku": (10.0 / 33.0, vec(m=1)), "sun": (1.0 / 33.0, vec(m=1)),
}
PREFIX = {"k": 1e3, "M": 1e6, "G": 1e9, "m": 1e-3, "u": 1e-6, "µ": 1e-6,
          "c": 1e-2, "d": 1e-1, "n": 1e-9}

# 同じ次元を持つ代表的な量（同じ次元＝同じ量、ではない点に注意）
NAMES = {
    vec(m=1): "長さ", vec(kg=1): "質量", vec(s=1): "時間",
    vec(m=1, s=-1): "速度", vec(m=1, s=-2): "加速度",
    vec(kg=1, m=1, s=-1): "運動量 / 力積（N·s）",
    vec(kg=1, m=1, s=-2): "力",
    vec(kg=1, m=2, s=-2): "エネルギー / 仕事 / トルク（同じ次元の別の量）",
    vec(kg=1, m=2, s=-3): "仕事率（電力）",
    vec(kg=1, m=-1, s=-2): "圧力 / 応力（剪断応力を含む）/ エネルギー密度",
    vec(kg=1, m=2, s=-1): "角運動量",
    vec(m=2, s=-2): "比エネルギー / 吸収線量（Gy）/ 線量当量（Sv）— Gy と Sv は別の量",
    vec(s=-1): "周波数（Hz）/ 放射能（Bq）",
    vec(kg=1, m=-3): "密度",
    vec(): "無次元",
}

_SUP = {"²": "^2", "³": "^3", "⁻¹": "^-1", "⁻²": "^-2", "·": "*", "×": "*", "⋅": "*"}


class ParseError(ValueError):
    pass


def _norm(text):
    for k, v in _SUP.items():
        text = text.replace(k, v)
    return text.replace(" ", "")


def _tokens(text):
    pattern = r"\d+\.?\d*(?:[eE][+-]?\d+)?|[A-Za-zµΩ]+|[*/^()]|[+-]?\d+"
    out, pos = [], 0
    while pos < len(text):
        m = re.match(pattern, text[pos:])
        if not m:
            raise ParseError(f"解釈できない文字: {text[pos:pos + 5]!r}")
        out.append(m.group(0))
        pos += m.end()
    return out


def _unit(name):
    if name == "Ω":
        name = "Ohm"
    if name in UNITS:
        return UNITS[name]
    if len(name) > 1 and name[0] in PREFIX and name[1:] in UNITS:
        scale, dims = UNITS[name[1:]]
        return scale * PREFIX[name[0]], dims
    raise ParseError(f"未知の単位: {name!r}")


def _mul(a, b, sign=1):
    return a[0] * (b[0] if sign > 0 else 1 / b[0]), tuple(x + sign * y for x, y in zip(a[1], b[1]))


def _pow(a, n):
    return a[0] ** n, tuple(x * n for x in a[1])


def parse(text):
    toks = _tokens(_norm(text))
    pos = 0

    def peek():
        return toks[pos] if pos < len(toks) else None

    def nxt():
        nonlocal pos
        pos += 1
        return toks[pos - 1]

    def atom():
        t = nxt()
        if t == "(":
            v = expr()
            if nxt() != ")":
                raise ParseError("括弧が閉じていません")
            return v
        if re.fullmatch(r"\d+\.?\d*(?:[eE][+-]?\d+)?", t):
            return float(t), vec()
        return _unit(t)

    def term():
        v = atom()
        if peek() == "^":
            nxt()
            e = nxt()
            if not re.fullmatch(r"[+-]?\d+", e):
                raise ParseError("指数は整数のみ対応です")
            v = _pow(v, int(e))
        return v

    def expr():
        v = term()
        while peek() in ("*", "/"):
            op = nxt()
            v = _mul(v, term(), 1 if op == "*" else -1)
        return v

    v = expr()
    if pos != len(toks):
        raise ParseError(f"余った入力: {toks[pos:]}")
    return v


def fmt(dims):
    parts = [f"{b}^{e}" if e != 1 else b for b, e in zip(BASE, dims) if e]
    return "[" + (" ".join(parts) if parts else "無次元") + "]"


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, args = argv[1], argv[2:]
    try:
        if cmd == "dim" and len(args) == 1:
            scale, dims = parse(args[0])
            print(f"{args[0]} -> 次元 {fmt(dims)}  SI換算係数 {scale:.6g}")
            print("同じ次元の量の候補: " + NAMES.get(dims, "（登録なし）"))
            return 0
        if cmd in ("same", "eq") and len(args) == 2:
            (sa, da), (sb, db) = parse(args[0]), parse(args[1])
            if da == db:
                print(f"一致: {fmt(da)}  （換算比 左/右 = {sa / sb:.6g}）")
                return 0
            diff = tuple(x - y for x, y in zip(da, db))
            print(f"不一致: 左 {fmt(da)} / 右 {fmt(db)}")
            print(f"左/右 の次元 = {fmt(diff)}  {NAMES.get(diff, '')}".rstrip())
            print("左 = 右 が成り立つには、右辺にこの次元の因子が足りない/余っている。"
                  " 別の量（例: 運動量とエネルギー）との取り違えを疑うこと。")
            return 1
        if cmd == "conv" and len(args) == 3:
            value, (sa, da), (sb, db) = float(args[0]), parse(args[1]), parse(args[2])
            if da != db:
                print(f"次元が違うため換算できません: {fmt(da)} vs {fmt(db)}")
                return 1
            print(f"{args[0]} {args[1]} = {value * sa / sb:.6g} {args[2]}")
            return 0
    except (ParseError, ValueError) as e:
        print(f"入力エラー: {e}", file=sys.stderr)
        return 2
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
