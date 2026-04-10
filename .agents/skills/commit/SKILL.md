---
name: commit
description: 変更内容を解析し、プロジェクトのルールに従ってコミットする
argument-hint: /commit
---

# commit スキル

現在の `git status` と `git diff` を確認してください。
その後、以下の「Commitizenと同じルール」に従ってコミットメッセージを作成し、直接コミットを実行してください。

## コミットルールの定義

フォーマット: `<type>: <subject>`

`<type>` の選択肢:

| type | 説明 |
|------|------|
| feat | 新機能 |
| fix | バグ修正 |
| docs | ドキュメントのみの変更 |
| style | コードの意味に影響を与えない変更（空白、フォーマットなど） |
| refactor | バグ修正も新機能追加も行わないコード変更 |

## 実行手順

1. `git status` で変更ファイルを確認する
2. `git diff` で変更内容を確認する
3. 変更内容から適切な `type` と `subject` を選ぶ
   - 複数の type にまたがる場合は、最も重要な変更に合わせる
   - `subject` は日本語で簡潔に（50文字以内目安）
4. 以下を実行する:
   ```bash
   git add .
   git commit -m "<type>: <subject>"
   ```

## 注意事項

- 対話型ツール（`git commit` のエディタ起動など）は使用しない
- `-m` オプションで直接メッセージを指定すること
- ステージングは `git add .` または変更ファイルを個別に指定する
