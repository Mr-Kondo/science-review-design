# science-review

小説・脚本・漫画・ゲームの科学技術描写を、科学・工学・作品内整合に分けて監修するスキル。考察・仮説・未完成のアイデアにも、成立条件、代替説明、案の比較と暫定推奨を返す。作品プロファイルや完成原稿は必須ではない。

## 配置と利用

共有本体は [.claude/skills/science-review](.claude/skills/science-review/SKILL.md)。Codex用の `.agents/skills/science-review` は共有本体への相対シンボリックリンク。

```text
$science-review 廃熱で小型装置を動かすアイデアの成立条件と代替案を比較して。
$science-review この考察の前提と結論のつながり、他にありうる説明を確認して。
$science-review notes/engine.md を監修し、レポートと計算を reviews/engine/ に保存して。本文は編集しない。
```

Claude Codeでは先頭を `/science-review` にする。Gemini Antigravity／Antigravity CLIでは、配置したスキルを自然文で指定する。ホストでの実読込はファイル配置の検査とは別に確認する。

保存は明示指定時、本文編集は明示的な編集依頼の範囲だけ行う。科学監修の結果は、現実の製品認証や専門家による査読の代替ではない。

## インストール・更新・アンインストール

### Skills CLIでmainの最新版を追跡する

Node.js 22.20.0以上とGitが必要（Skills CLI 1.7.6で確認）。計算補助コードにはPython 3.10以上も必要（標準ライブラリのみ。標準出力・標準エラーはUTF-8）。**既存配置がある場合は、先に下の移行手順で退避する。CLIは既存ファイルを置換し、自動バックアップを作らない。**

初回だけGitHubの取得元を登録する。

```sh
npx skills add Mr-Kondo/science-review-design#main --skill science-review --global --agent claude-code codex antigravity antigravity-cli --yes
# 次回以降、このスキルだけを更新
npx skills update science-review --global
# CLI管理の配置を削除
npx skills remove science-review --global --yes
```

登録後は `npx skills update` でも更新できるが、他の登録済みスキルも対象になる。更新先は最新Releaseのタグではなく **mainのスキルフォルダ**。版番号の比較ではなくフォルダの変更を追跡する。タグへ固定した導入はmain追従にならない。

CLI 1.7.6では `~/.agents/skills/science-review/` に本体を置き、Codex・Antigravity IDE/CLIはこの共有配置を使い、Claude Codeにはリンクを作る（リンク失敗時はコピー）。旧Python版のAntigravity IDE配置先 `~/.gemini/config/skills/` とは異なるため、登録時の配置表示を確認する。プロジェクト配置は、**このソースリポジトリ以外の利用先**で初回登録の `--global` を外して実行し、更新は `npx skills update science-review --project`、削除は `npx skills remove science-review --yes` とする。ソースリポジトリ自身に実行すると本体を上書きするおそれがある。

#### 旧Pythonインストーラー（2.2.1以前）の配置から移行する

1. 利用ホストを閉じる。旧インストーラーの4配置先（`~/.agents/skills/`、`~/.claude/skills/`、`~/.gemini/config/skills/`、`~/.gemini/antigravity-cli/skills/` の各 `science-review/`）、および `~/.codex/skills/science-review/` 等の同名配置・リンクを確認する。ローカル変更があれば保持する。
2. 既存の各 `science-review/` を、スキル探索対象外のバックアップ先へ移す（例：各 `skills/` の親の `science-review-backups/` 以下に重複しない名前で退避）。リンクの場合はリンク先を確認し、本体を消さない。旧インストーラーの管理ファイル `.science-review-install.json` が残る配置も、そのまま退避する。
3. 上の `skills add` を実行する。登録後はCLIで管理する。CLIのlockファイルは手動作成・編集しない。
4. 旧Antigravity IDE配置を引き続き必要とする環境では、退避した `~/.gemini/config/skills/science-review` の代わりにCLIの本体へのリンクを作る。この互換リンクはCLI管理外なので、削除時はリンクだけを別途取り除く。リンクを使えない環境では、旧配置が必要なホストを使わない。
5. 登録された取得元・本体9ファイル・参照リンクを確認し、ホストを再起動する。更新後もローカル変更を保持する必要がある場合は、CLI更新前に別途退避する。配置確認だけでは製品上の読込成功を保証しない。

移行で退避したコピーは、配置照合と利用確認後に削除する。途中失敗した場合は保持し、退避コピーから復旧する。

## 検査

Python 3.10以上、スキル付属のPythonコードは標準ライブラリのみを使用する。

```sh
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s tests/science-review -v
python3 .agents/skills/science-review/scripts/dimcheck.py conv 36 km/h m/s
python3 .agents/skills/science-review/scripts/dimcheck.py eq J 'kg*m²/s²'
```

[評価入力・手順](evals/science-review/README.md)と[検査記録](evals/science-review/verification-results.md)を参照。実行結果・検証用ファイル・モデルの全ログは `feedback/` に保持し、Gitには含めない。公開する評価概要と匿名fixtureを区別している。

[GitHub ActionsのCI](https://github.com/Mr-Kondo/science-review-design/actions/workflows/ci.yml)は、Linux・Windows・macOSとPython 3.10・3.14の計6構成で、上記2つの検査スイートを実行する。更新用ツールの検査、スキルの構成・評価ケースの整合、計算補助コードの検査を含む。製品アプリ上の起動・モデルの判断・専門家評価はCIの検査対象に含めない。

## 設計の由来

[配布・検証・出力契約のADR](adr/delivery-and-output-contracts.md)に、今回の判断、採用しなかった案、成功指標を記録している。指定見出し・表の列・残す節はテンプレートより優先する。通常利用での自動保存と汎用評価基盤の追加は行わない。

2.1.0の少数例比較では指定構造を保持したが、冒頭の判定と計算結論の不整合、未出典の性能値の付加が変更前後とも残った。[Issue #2](https://github.com/Mr-Kondo/science-review-design/issues/2)で追跡し、科学判断の精度向上は主張しない。

版2.2.0では、配置するファイルを35個から9個（約55 KB）に絞った。評価データ・評価記録・テストは配置しない。経緯と判断は[配布物の絞り込みADR](adr/slim-package.md)と[Issue #7](https://github.com/Mr-Kondo/science-review-design/issues/7)に記録した。2.1.1までの経緯は[リリースと配置のADR](adr/wikiskill-release-delivery.md)にある。
版2.2.1では[Skills CLI対応ADR](adr/skills-cli-update.md)に従い、評価・テストをスキルフォルダ外へ移す。配布9ファイルと科学監修の指示本文は2.2.0と同じ。
Pythonインストーラー（`tools/install.py`・`tools/uninstall.py`・配布一覧）は[削除のADR](adr/remove-python-installer.md)に従い廃止した。導入と更新はSkills CLIだけで行う。

更新時だけ使う[知識索引](knowledge/index.md)と[有限比較のADR](adr/wikiskill-trial.md)は、[Issue #4](https://github.com/Mr-Kondo/science-review-design/issues/4)の検証用。通常の監修やインストールには知識層を追加しない。
`python3 tools/wiki_eval.py --help` で計画凍結・実行・採点確認の手順を確認できる。ログは新しい `feedback/` の実行フォルダへ保存し、同じ試行を上書きしない。索引の比較と候補スキルの比較を分け、改善が示されなければ候補を採用しない。

[2026-11-03の比較結果](docs/wiki-trial-results.md)では索引なし／ありが同点、候補は反復改善と回帰なしの条件を満たさず不採用。更新用索引・比較ツールはリポジトリとリリースのソースアーカイブに含め、通常のスキル配置には含めない。
このツールは本件専用であり、第一段階には非公開の既存ST02/ST03記録が必要なため、cloneだけでは実行できない。
Claude Code 2.1.316のsafe-mode等を前提にし、別CLI版の互換性は未確認。user設定は接続先のため保持し、空の一時cwdで実行する。
実行には既存のモデル利用契約を使う。以下のrunはモデルを呼び出すため、再検証の予算・採点規則を先に決める。

```sh
python3 tools/wiki_eval.py freeze maintenance feedback/new-trial-maintenance
python3 tools/wiki_eval.py run feedback/new-trial-maintenance
python3 tools/wiki_eval.py summarize feedback/new-trial-maintenance feedback/new-trial-maintenance-scores.json
python3 tools/wiki_eval.py freeze quality feedback/new-trial-quality --candidate feedback/candidate-SKILL.md --selection feedback/selection.json
python3 tools/wiki_eval.py run feedback/new-trial-quality
python3 tools/wiki_eval.py summarize feedback/new-trial-quality feedback/new-trial-quality-scores.json
```

採点JSONは `scores` 配列に各試行の `id`、全軸の真偽値を持つ `axes`、根拠の `evidence` を記す。
試行IDと軸・規則は凍結plan.jsonにある。selection.jsonには `maintenance_directory`、`maintenance_summary_sha256`、`candidate_sha256`、`target_axis`（今回は `consistent`）、`reason` が必要。
それぞれ完了済み第一段階のパス、summary.jsonのSHA-256、候補のSHA-256、事前に選ぶ対象軸、選択理由を指定する。
凍結後にコード・CLI版・入力が変わった場合や途中失敗時は停止し、同じフォルダの再開・上書きはしない。新しい計画を使う場合も原因と追加呼出の扱いを記録する。

[実装指示](claude-code-implementation-prompt.md)、[設計書](research-and-design.md)、[固定版の元資料](source-manifest.json)、[設計出典・確認状態](.claude/skills/science-review/references/design-sources.md)を保持している。元資料の取得履歴と今回の新版の検査結果は別記録。未確認のライセンスを推定して付与していない。
