---
status: accepted
date: 2026-11-11
decision-makers: user, Claude Code
supersedes-in-part: slim-package.md, skills-cli-update.md, delivery-and-output-contracts.md, wikiskill-release-delivery.md
---

# Pythonインストーラーを削除し、導入と更新をSkills CLIに一本化する

## 背景と仮説

`npx skills add/update/remove`（[skills-cli-update.md](skills-cli-update.md)）でmainへの追従と削除ができるようになり、`tools/install.py` と `tools/uninstall.py` は同じ役割の二重経路になった。ユーザーは「npxで導入できるなら、install.pyはかえって煩雑」と判断した。

- 仮説：Skills CLIだけで導入・更新・削除が足りれば、Python版の約230行、専用テスト約330行、配布一覧、READMEの説明約70行、WindowsのPowerShell検査を持つ費用に見合わない。
- 失うもの：ハッシュによる変更保護、更新前バックアップ、失敗時の復旧、Gitなしのアーカイブからの導入、Windowsでのコピー方式導入、バージョン定数（`VERSION`）。
- 読むべき指標：Skills CLIでの登録・更新・削除が動くこと（Mac移行は2.2.1で完了、公開後のmain更新で確認）。CLIでは足りない利用環境が報告されたら、この決定を見直す。

## 決定

次を削除する。置換先は作らない。

- `tools/install.py`、`tools/uninstall.py`、`tools/package-files.json`
- `tests/test_installation.py`（インストーラー専用。配布物一致の確認は、CLIがスキルフォルダ全体を配るため不要）
- READMEの「Pythonインストーラーで管理する」節とWindows CIのPowerShell実行
- `evals/science-review/README.md` のインストーラーへの言及

旧配置からの移行手順は、Python版が作った配置を退避してCLIで登録し直す説明としてREADMEに残す。`tools/wiki_eval.py` は別目的のため残す。

## 影響と代替案

- 版番号の置き場所：`install.py` の `VERSION` はなくなり、版はGitタグとリリースだけで表す。
- 配置の管理：CLIの配置にはPython版の変更保護とバックアップがない。手動変更したい利用者はCLI更新前に退避する。
- Windows・Node.jsなしの環境：導入にはNode.js 22.20.0以上が必要になる。Nodeを使えない場合は、スキルフォルダを手動でコピーする。
- 旧ADRの記述（installer、package-files.json）は当時の決定として残し、先頭に本ADRへの参照を付けた。
- 代替案：Python版を残し「非推奨」と記す案は、保守対象とテストが残るため不採用。

## 非機能要件

追加依存なし。削除のみで、モデルAPI・秘密情報・個人情報への影響はない。Skills CLIが配布する9ファイルと指示本文は変えない。
