---
status: accepted
date: 2026-11-05
decision-makers: user, Codex
supersedes-in-part: slim-package.md
superseded-in-part-by: remove-python-installer.md
---

# Skills CLIの標準登録でmainへの更新を可能にする

## 背景と4つの設計事項

[Issue #11](https://github.com/Mr-Kondo/science-review-design/issues/11)。Pythonインストーラーの配置はSkills CLIのlockに登録されず、`npx skills update` だけでは更新されない。ユーザーは既存設計を踏まえた最小改修を選び、以下の設計を承認した。

- 仮説：標準の `skills add` でGitHubのmainを登録すれば独自アップデーターなしで追従できる。
- 要件と調査：CLI 1.7.6、Node.js 22.20.0以上。CLIはスキルフォルダ全体を配布し、フォルダのハッシュで変更を判定する。`official-prompt-tailor` と `mece-cluster-advisor` の初回登録、main追従、管理方式の分離、退避手順を採用する。frontmatterのname・descriptionとreferences/assets/scriptsの構成を維持する。独自登録処理や追加依存は採用しない。
- README駆動：初回登録・更新・削除・旧配置からの移行をREADMEの先頭の導入手順として示す。
- モデル：RuntimePackage（本体9ファイル）、RepositoryEvidence（評価・テスト・履歴）、Installation（Python管理またはCLI管理）を分離する。同一配置を両方式で更新しない。

## 決定

`evals/` を `evals/science-review/`、スキルの `tests/` を `tests/science-review/` へ移す。runtimeの重複コピーや生成工程は追加しない。配布対象の全追跡ファイルと `tools/package-files.json` の一致を検査する。Python版のinstall/update/uninstallは維持し、配送変更を2.2.1として記録する。

main追従のCLI導入を選択可能にし、CLIのlockを手動編集しない。移行前の配置とローカル変更は探索対象外に退避する。CLIにはPython版の変更保護とバックアップを期待しない。旧Antigravity IDE配置が必要なら共有本体への互換リンクを用い、CLI管理外として削除方法を明記する。

監修指示・計算ロジック・匿名fixture・評価JSONを変えない。科学判断の改善とIssue #2は対象外。履歴のコマンドは当時のまま残し、現行の実行先を別記する。

## 影響と代替案

評価用Pythonとリンク先を変更する費用が生じるが、配布用コピーの継続同期より管理箇所を少なくできる。旧ADRの「同じ場所に残す」決定だけを置き換える。

- 現状のフォルダをそのままCLIで配布：変更は少ないが評価・テストも利用者へ配布されるため不採用。
- 配布用フォルダを別途生成・追跡：元の配置を保てるが、同期処理と二重管理が増えるため不採用。
- 独自のlock登録機能：CLIの内部形式への依存が増えるため不採用。

## 実装と検証

変更先：README、CI、`.gitignore`、`tools/install.py`、`tools/wiki_eval.py`、`tests/test_installation.py`、`tests/test_wiki_eval.py`、移動した評価・テスト、knowledgeのリンク。古い凍結試行はハーネス変更により再開できない。新試行は新しいfeedbackディレクトリへ保存する。

- [x] Pythonの両テストスイートが成功する。
- [x] 配布一覧とスキルフォルダの全追跡ファイルが一致し、runtime9ファイルは2.2.0とバイト一致する。
- [ ] 隔離環境でCLIの登録、取得元・ハッシュの記録、更新、削除を確認する。
- [x] 独立レビューを実施し、根拠のある指摘を採用する。
- [ ] 公開後、Macの既存配置を保護して移行・照合し、一時物を片付ける。

成功指標は9ファイルの維持、mainの変更検出と取得、既存検査の成功。誤った取得元・余分な配布・既存ファイルの喪失が見つかれば移行を止め、バックアップから復旧する。モデル比較は指示本文を変更しないため実施しない。隔離した登録結果の2.2.0対2.2.1比較は配送検証であり、判断品質のA/B評価ではない。

## 非機能要件と根拠

追加Python依存なし。Node/npmとGitはCLI方式だけに必要。CLIはネットワークを使用するがモデルAPIは呼ばない。秘密情報・端末の絶対パス・全ログは公開せず `feedback/` に置く。CLIのtelemetryは検証・Mac移行時に `DISABLE_TELEMETRY=1` で無効化する。導入説明は通常のMarkdownとテキストコマンドで提供し、ライセンスの推定追加はしない。

- [Skills CLI公式](https://github.com/vercel-labs/skills)
- [更新実装](https://github.com/vercel-labs/skills/blob/main/src/update.ts)
- [旧配布ADR](slim-package.md)

## 検証記録（公開前）

2026-11-05、macOS、Python 3.15.2、Skills CLI 1.7.6、Node.js 22.22.0：既存28テストと移動後12テストが成功。quick_validateも成功（ホストPythonにPyYAMLがないため、既存のuv実行環境を使用）。runtime9ファイルと、移動した評価資料のうちリンク更新を伴わない21ファイルは変更前とバイト一致する。

隔離したHOME・XDG領域で、新配置からのローカル導入が9ファイル・Claudeリンクを作り、削除も成功した。GitHubの公開前mainから別の隔離ホームへ登録すると35ファイルとなり、取得元とフォルダハッシュが記録された。公開後の更新はこの登録で検証する。初回検査ではAntigravityにも個別リンクができると仮定したassertが失敗したが、実際はCLIが共有配置を使うことを確認し検査とREADMEを修正した。成功済み導入は繰り返していない。

この検査はCLI配送の確認であり、3製品の実読込や科学判断の品質は再評価していない。

独立レビュー：Claude Code 2.1.317、claude-sonnet-5-5、medium。重大な不具合の指摘なし。履歴文書の旧パスに現行配置を注記する指摘を採用した。未追跡の旧テストキャッシュを配布する懸念は、CLIの `__pycache__` 除外と実際の9ファイル照合で発生しないため、追加の配布処理は採用しない。レビューはCLIのネットワーク動作・製品の実読込を検証していない。レビュー中に意図しないintent-to-add操作があり、レビュアー自身が対象ファイルだけ戻した。内容の変更はない。
