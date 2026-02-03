---
name: start-feature
description: 新機能の実装やバグ修正を開始します。ユーザーの要望に基づき、連番ディレクトリの作成、計画の立案(plan.md)、承認フロー、実装、品質チェックまでを管理します。
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# 実装開始ワークフロー

あなたはプロジェクトのリードエンジニアです。以下の厳格なルールに従い、実装プロセスを遂行してください。

## 参照ドキュメント
- [実装ワークフロー詳細](references/workflow.md)

## 🚨 重要: 絶対順守ルール
1. **許可前のコード変更禁止**:
   - `plan.md` を作成し、ユーザーの明示的な許可を得るまでは、プロダクトコード（`mb_scanner/`）を一切変更してはいけません。
2. **記録の徹底**:
   - ユーザーからの指示や変更内容は、必ずタスクディレクトリ内の `prompt.md` に記録し続けてください。

## 開始手順 (Initialization)

ユーザーの要望（`$ARGUMENTS`）を受け取ったら、以下のステップで初期化を行ってください。

1. **機能名の決定**:
   - ユーザーの要望内容から、適切で簡潔な英語の機能名（kebab-case）を生成してください。
   - 例: "CSVエクスポート機能が欲しい" → `add-csv-export`
   - 例: "バグ修正: 検索が遅い" → `fix-search-latency`

2. **ディレクトリ作成**:
   - 決定した機能名を引数にして、以下のスクリプトを実行してください。
   ```bash
   # 例: uv run python .claude/skills/start-feature/scripts/init_task.py add-csv-export
   uv run python .claude/skills/start-feature/scripts/init_task.py <GENERATED_KEBAB_NAME>
   ```

3. **プランニング**:
    - 自動生成された plan.md を読み込み、ユーザーの要望に合わせて編集・提案してください。

---
