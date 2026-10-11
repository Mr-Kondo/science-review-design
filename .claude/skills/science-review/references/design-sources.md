# 設計出典と確認状態

確認日：2026-10-11。Mは手法・形式の由来であり、個別科学主張のEではない。本スキルの有効性や実装の正しさを外部資料の存在で保証しない。

## M00 同梱設計と元スキル

今回、ローカルの `claude-code-implementation-prompt.md`、`research-and-design.md`、`source-manifest.json`、`source-snapshot/` の5ファイルを読んだ。元スキルはMr-Kondo/Project_Defyの `defy-science-review`、固定コミット `8a94b0e557ce6db4b98323fd8f31a92f75d1fdbb`。確認方法はローカル読取。5ファイルのGit blob SHA-1を再計算し、同梱manifestとの一致を確認した。これは取得元サーバーや最新版の再確認ではない。

| 固定版の参照先 | manifestと一致したblob |
| --- | --- |
| [SKILL.md](https://github.com/Mr-Kondo/Project_Defy/blob/8a94b0e557ce6db4b98323fd8f31a92f75d1fdbb/.claude/skills/defy-science-review/SKILL.md) | 01747097f0fc6e7dc6d1af1b32af4bfcb7be345c |
| [defy-context.md](https://github.com/Mr-Kondo/Project_Defy/blob/8a94b0e557ce6db4b98323fd8f31a92f75d1fdbb/.claude/skills/defy-science-review/references/defy-context.md) | bd59f1659b79c7db4bff6adf0126478a62638e51 |
| [methods-and-sources.md](https://github.com/Mr-Kondo/Project_Defy/blob/8a94b0e557ce6db4b98323fd8f31a92f75d1fdbb/.claude/skills/defy-science-review/references/methods-and-sources.md) | ad51257b627f78e2f37d9552cfbef3911cfaef8e |
| [evaluation-cases.md](https://github.com/Mr-Kondo/Project_Defy/blob/8a94b0e557ce6db4b98323fd8f31a92f75d1fdbb/.claude/skills/defy-science-review/references/evaluation-cases.md) | 0937380bb79439761044e343338378427c438fe6 |
| [dimcheck.py](https://github.com/Mr-Kondo/Project_Defy/blob/8a94b0e557ce6db4b98323fd8f31a92f75d1fdbb/.claude/skills/defy-science-review/scripts/dimcheck.py) | 761f812b059b83d34d2cd268017010d6b826fc99 |

継承：三軸、能力段階、確定・提案・人物認識の区別、工程の境界、出典・計算ID、最小の説明修正、本文編集との分離。改善：A/Bを最終表まで分離、関連資料検索、相談モード、情報不足と反証の区別、匿名fixture、境界入力・意味の異なる量の換算拒否。

文章とPythonパーサーは本要件に基づいて新規に記述した。元の実装コード・外部スキルの文言を転載していない。元資料のライセンスは今回確認しておらず、推定のライセンスを付与しない。単位の尺度・次元は物理的定義として記載し、原版の評価実績を新版の実績へ転記しない。

## 今回確認した外部資料

取得方法はWebツールによるHTML抽出。原文との逐語照合はしていない。年・改訂が該当表示で確認できないものは未確認。以下は要約であり引用ではない。

| ID・資料とURL | 版・確認箇所・閲覧状態 | 採用内容と限界 |
| --- | --- | --- |
| M01 [Agent Skills specification](https://agentskills.io/specification) | 版表示未確認。Frontmatter、name、description、metadata、Progressive disclosure、File references。抽出本文 | 命名、description 1024文字以内、段階的読込。形だけで成果品質を保証しない |
| M02 [OpenAI Build skills](https://developers.openai.com/codex/skills/) | [転送先](https://learn.chatgpt.com/docs/build-skills)。Where Codex loads local skills、Create a skill。版未確認、抽出本文 | `.agents/skills`、symlinkを使う配置。Codexは `$science-review` で呼ぶ。実機での起動成功は別検査 |
| M03 [Claude Code Skills](https://code.claude.com/docs/en/skills) | Choose where skills load、Available string substitutions。版未確認、抽出本文 | `.claude/skills` と `$ARGUMENTS`。argument-hintをportableなmetadataへ移したためヒント表示は保証しない。allowed-toolsで非編集を強制しない |
| M04 [NASA SEH 5.0 Product Realization](https://www.nasa.gov/reference/5-0-product-realization/) | 5.0の概要と5.3 verification・5.4 validationへの説明。版未確認、抽出本文 | 製作・調達・統合、仕様確認と使用目的への適合の区別。宇宙機工程を全適用せず、個別物理現象の根拠にしない |
| M05 [NIST SP 811 Chapter 7](https://www.nist.gov/pml/special-publication-811/nist-guide-si-chapter-7-rules-and-style-conventions-expressing-values) | 7.2、7.7、7.9の表記。Web改訂日未確認、抽出本文 | 数値・単位の空白と、範囲・不確かさの帰属を明確にする。モデルの正しさを保証しない |
| M06 [SymPy Unit Systems](https://docs.sympy.org/latest/modules/physics/units/index.html) | 1.14.0表示、Unit Systemsの次元・尺度換算。抽出本文 | 次元と換算の区別。今回SymPyは導入・実行していない |
| M07 [JCGM GUM-6:2020](https://www.bipm.org/en/doi/10.59161/jcgmgum-6-2020) | DOI 10.59161/JCGMGUM-6-2020。書誌・抄録のみ | 測定モデルという主題だけ。PDF本文未読、正式な不確かさ計算の規定として使わない |

## 指定された比較資料：今回は原文を再確認していない

下記の位置・版は同梱設計書の報告。今回の閲覧状態は未確認（ローカル設計書の二次記録のみ）、確認日は2026-10-11。個別科学の支持や転載には使わず、一括インストール・API実行もしない。過去の読了状態を今回の読了として扱わない。

| 指定URL／DOI | 設計書に記録された範囲 | 利用する考え方・限界 |
| --- | --- | --- |
| [Anthropic skill-creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md) | SKILL本文、blob 65b3a402dbd09b8e83f9d637c6b553875189085c | 入力・期待判断の固定、スキル有無比較。補助コード転載なし |
| [K-Dense scientific-critical-thinking](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/scientific-critical-thinking/SKILL.md) | v1.5、Appraisal Workflow | 証拠と推論、未報告と反証の区別。GRADEを工学へ一律適用しない |
| [K-Dense peer-review](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/peer-review/SKILL.md) | v2.4、Review workflow | 再実行性・具体的指摘。論文査読の権限手順は導入しない |
| [K-Dense literature-review](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/literature-review/SKILL.md) | v1.11、検索・引用照合 | 取得状態の透明性。網羅検索・図生成を必須化しない |
| [Kirby 2003 Scientists on the Set](https://doi.org/10.1177/0963662503123005) | 大学書誌・抄録のみと記録 | 科学監修と物語目的の関係という示唆。本スキルの修正順は独自設計 |
| [Kirby 2010 The Future Is Now](https://doi.org/10.1177/0306312709338325) | 大学書誌・抄録のみと記録 | 作中で動く技術と現実の実証を分ける。本文未読 |
| [Kassis et al. 2026 Scientific Agent Skills](https://doi.org/10.48550/arXiv.2609.00065) | arXiv v2書誌・抄録のみと記録 | 設計背景のみ。今回書誌・本文を再確認せず、監修精度の保証にしない |

ローカルのCodex標準 `skill-creator/SKILL.md` も読んだ。段階的読込とユーザーの作業範囲を保つ方針を採用した。これは製品同梱の手順であり、上記Anthropic版の読了ではない。
