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

Python 3.10以上が必要。Windowsでは以下の `python3` を `python` と読み替え、`python --version` でバージョンを確認する。追加パッケージやGitはスクリプトの実行に不要。

スクリプトと計算補助ツールの標準出力・標準エラーはUTF-8。別のプログラムから呼び出す場合もUTF-8で読み取る。

このリポジトリをcloneするか、[リリース](https://github.com/Mr-Kondo/science-review-design/releases)のソースアーカイブを展開して、そのフォルダで実行する。

```sh
# インストール。ユーザー用のCodex、Claude Code、Antigravity IDE/CLIへコピーする
python3 tools/install.py
# 更新。新しい版のリポジトリ／アーカイブから同じコマンドを実行する
python3 tools/install.py
# アンインストール
python3 tools/uninstall.py
```

既定では次の4配置先へコピーする。`--target` で一つに限定できる。コピー方式のため、シンボリックリンクの作成権限は不要。インストール・更新後は対象ホストを再起動する。

| target | ユーザー配置先 |
| --- | --- |
| `codex` | `~/.agents/skills/science-review/` |
| `claude` | `~/.claude/skills/science-review/` |
| `antigravity` | `~/.gemini/config/skills/science-review/` |
| `antigravity-cli` | `~/.gemini/antigravity-cli/skills/science-review/` |

Antigravityの配置先は2026-10-31時点の比較先スキルの実装に基づく。IDE／CLIでの実読込は未確認。

プロジェクト配置ではClaude Codeは `.claude/skills/`、他は共通の `.agents/skills/`。`--target all` は重なる配置先を一度だけ処理する。
プロジェクトでCodex／Antigravityのいずれかを指定して削除すると、この共通配置を利用する他ホストからも使えなくなる。

特定のプロジェクトに配置する場合は、存在するプロジェクトフォルダを指定する。更新・削除にも同じオプションを使う。

```sh
python3 tools/install.py --scope project --project-dir /path/to/project --target codex
python3 tools/uninstall.py --scope project --project-dir /path/to/project --target codex
# 実行前の確認。書き込み・削除は行わない
python3 tools/install.py --dry-run
python3 tools/uninstall.py --dry-run
```

管理用ファイル `.science-review-install.json` に配置したファイルのSHA-256を記録する。更新・削除は、このスクリプトで配置した内容がそのまま残っている場合だけ行う。変更・欠落・追加ファイル、手動コピー、シンボリックリンクがある場合は停止する。必要な内容をバックアップし、対象の `science-review/` フォルダを別の場所へ移してから再実行する。他のスキルや親フォルダは削除しない。Pythonが生成した `__pycache__/*.pyc` は変更扱いにしない。

更新で置換と復旧の両方が失敗した場合は、元の配置を一時退避先に残し、その場所をエラー出力に表示する。

正常な更新でも、置換前の配置を `skills/` の親の `science-review-backups/` に保存し、`backup:` に場所を表示する。スキル探索対象の外に置き、自動削除しない。バックアップが失敗した場合は置換しない。
名前は更新先の版・UTC日時・乱数を含む。削除後もバックアップは残る。プロジェクト配置ではバックアップもプロジェクト内になるため、内容を確認し、Gitへの追加・公開を避ける。
同一内容の再インストールでもバックアップは増える。Windowsでは深いプロジェクトパスを避け、OSのパス長制限に注意する。

[配布一覧](tools/package-files.json)にあるスキル本体・参照資料・テンプレート・補助コード・匿名評価データと検査だけをコピーする。ローカルで追加したファイルは一覧になければ配布しない。一覧の更新時は追跡ファイルとの一致をテストで確認する。ローカルのモデル実行ログや設計書の原本はコピーしない。全配置先を事前検査してから処理するが、途中のOSエラーでは一部だけ処理済みになる場合がある。エラーを解消して同じコマンドを再実行する。同じ配置先への更新・削除を同時に実行しない。

WindowsのPowerShell 7で以下をリポジトリのルートから実行すると、検証用プロジェクトへのインストール・更新・削除を試せる。検証先は `feedback/` 内に新規作成し、終了時に片付ける。このブロックをWindows CIでも実行する。Windows PowerShell 5.1は今回の検証対象に含めない。

<!-- docs-smoke:start -->
```powershell
$ErrorActionPreference = 'Stop'
$project = Join-Path (Get-Location) ('feedback/日本語 project-' + [guid]::NewGuid())
New-Item -ItemType Directory -Path $project -Force | Out-Null
try {
    foreach ($script in @('install.py', 'install.py', 'uninstall.py')) {
        $scriptPath = Join-Path 'tools' $script
        python $scriptPath --scope project --project-dir $project --target all
        if ($LASTEXITCODE -ne 0) { throw "$script failed: $LASTEXITCODE" }
    }
} finally {
    Remove-Item -LiteralPath $project -Recurse -Force
}
```
<!-- docs-smoke:end -->

## 検査

Python 3.10以上、スキル付属のPythonコードは標準ライブラリのみを使用する。

```sh
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s .claude/skills/science-review/tests -v
python3 .agents/skills/science-review/scripts/dimcheck.py conv 36 km/h m/s
python3 .agents/skills/science-review/scripts/dimcheck.py eq J 'kg*m²/s²'
```

[評価入力・手順](.claude/skills/science-review/evals/README.md)と[検査記録](.claude/skills/science-review/evals/verification-results.md)を参照。実行結果・検証用ファイル・モデルの全ログは `feedback/` に保持し、Gitには含めない。公開する評価概要と匿名fixtureを区別している。

[GitHub ActionsのCI](https://github.com/Mr-Kondo/science-review-design/actions/workflows/ci.yml)は、Linux・Windows・macOSとPython 3.10・3.14の計6構成で、上記2つの検査スイートを実行する。インストール・更新・削除、日本語・空白を含むパス、変更の保護、更新失敗時の復旧、配置したスキルの補助コードと検査の実行を含む。WindowsではREADMEのPowerShell 7ブロックも実行する。製品アプリ上の起動・モデルの判断・専門家評価はCIの検査対象に含めない。

## 設計の由来

[配布・検証・出力契約のADR](adr/delivery-and-output-contracts.md)に、今回の判断、採用しなかった案、成功指標を記録している。指定見出し・表の列・残す節はテンプレートより優先する。通常利用での自動保存と汎用評価基盤の追加は行わない。

2.1.0の少数例比較では指定構造を保持したが、冒頭の判定と計算結論の不整合、未出典の性能値の付加が変更前後とも残った。[Issue #2](https://github.com/Mr-Kondo/science-review-design/issues/2)で追跡し、科学判断の精度向上は主張しない。

[実装指示](claude-code-implementation-prompt.md)、[設計書](research-and-design.md)、[固定版の元資料](source-manifest.json)、[設計出典・確認状態](.claude/skills/science-review/references/design-sources.md)を保持している。元資料の取得履歴と今回の新版の検査結果は別記録。未確認のライセンスを推定して付与していない。
