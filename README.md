# science-review

小説・脚本・漫画・ゲームの科学技術描写を、科学・工学・作品内整合に分けて監修するスキル。考察・仮説・未完成のアイデアにも、成立条件、代替説明、案の比較と暫定推奨を返す。作品プロファイルや完成原稿は必須ではない。

## 配置と利用

共有本体は [.claude/skills/science-review](.claude/skills/science-review/SKILL.md)。Codex用の `.agents/skills/science-review` は共有本体への相対シンボリックリンク。

```text
$science-review 廃熱で小型装置を動かすアイデアの成立条件と代替案を比較して。
$science-review この考察の前提と結論のつながり、他にありうる説明を確認して。
$science-review notes/engine.md を監修し、レポートと計算を reviews/engine/ に保存して。本文は編集しない。
```

Claude Codeでは先頭を `/science-review` にする。別プロジェクトへ導入する場合は、スキル本体をそのプロジェクトの `.claude/skills/science-review/` または `.agents/skills/science-review/` にコピーする。シンボリックリンクを使う場合はリンク先の本体も必要。

保存は明示指定時、本文編集は明示的な編集依頼の範囲だけ行う。科学監修の結果は、現実の製品認証や専門家による査読の代替ではない。

## 検査

Python 3.10以上、スキル付属のPythonコードは標準ライブラリのみを使用する。

```sh
python3 -m unittest discover -s .claude/skills/science-review/tests -v
python3 .agents/skills/science-review/scripts/dimcheck.py conv 36 km/h m/s
python3 .agents/skills/science-review/scripts/dimcheck.py eq J 'kg*m²/s²'
```

[評価入力・手順](.claude/skills/science-review/evals/README.md)と[検査記録](.claude/skills/science-review/evals/verification-results.md)を参照。モデルの全ログと作業端末の絶対パスを含む記録はローカルで保持し、Gitには含めない。公開する評価概要と匿名fixtureを区別している。

## 設計の由来

[実装指示](claude-code-implementation-prompt.md)、[設計書](research-and-design.md)、[固定版の元資料](source-manifest.json)、[設計出典・確認状態](.claude/skills/science-review/references/design-sources.md)を保持している。元資料の取得履歴と今回の新版の検査結果は別記録。未確認のライセンスを推定して付与していない。
