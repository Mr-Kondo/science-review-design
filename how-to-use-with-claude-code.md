# Claude Codeへの渡し方

この一式は設計・実装指示です。スキル本体はClaude Codeがこれから作成します。

## 資料一式を使う方法

1. `science-review-design.zip` をダウンロードして解凍します。
2. 作成先のプロジェクトフォルダへ、解凍した `science-review-design` フォルダを置きます。
3. そのプロジェクトをClaude Codeで開き、次の文を送ります。

```text
science-review-design/claude-code-implementation-prompt.md を読み、区切り以降の実装指示に従って science-review スキルを実装してください。
追加資料は同じフォルダの research-and-design.md と source-snapshot/ にあります。
科学監修に加え、考察・仮説・未完成のアイデアへの助言にも対応してください。
計画だけで終えず、ファイル作成と実行できる検査まで完了し、未実施の検査は明記してください。
```

既定の作成先はそのプロジェクトの `.claude/skills/science-review/` です。Defyのプロジェクトへ置いても、汎用版は既存スキルと別の名前で作成します。

全プロジェクトで使える個人用スキルにしたい場合は、上の依頼文に「保存先はプロジェクト内ではなく `~/.claude/skills/science-review/` にしてください」と追加します。作成先の書込権限はClaude Codeの環境で扱われます。

## ファイルを置かずに渡す方法

`claude-code-implementation-prompt.md` を開き、最初の `---` より下をすべてClaude Codeに貼り付けます。プロンプト単独でも実装できるようになっています。

## 実装後の利用例

実装完了後、新しいClaude Codeセッションで `/science-review` の認識を確認して使います。

```text
/science-review 体の廃熱で小型装置を動かすアイデアを相談したい。成立条件と代替案を比較して。
/science-review この考察の前提から結論までに飛躍がないか、他にありうる説明も示して。
/science-review chapters/scene-03.md の装置を、電源と排熱を中心に監修して。
```

相談では原稿や作品プロファイルがなくても始められます。資料にない条件は仮定・提案として扱い、採用や本文への反映は作者が決めます。
