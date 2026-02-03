# 拡張実装ガイド

新機能を追加する際は、以下の該当するセクションの手順に従って実装してください。アーキテクチャのレイヤー構造（CLI -> Workflows -> Services -> Lib）を遵守すること。

## 1. 新しい CLI コマンドの追加
新しい機能（例: 新しい分析モードなど）をCLIに追加する手順です。

1. **ファイル作成**: `mb_scanner/cli/` に新しいPythonファイルを作成します。
2. **コマンド定義**: `Typer` を使用してコマンドと引数を定義します。
3. **Workflow実装**: ビジネスロジックが複雑な場合は、`mb_scanner/workflows/` に新しいWorkflowクラスを作成します。
4. **登録**: `mb_scanner/cli/__init__.py` に新しいコマンドを登録し、メインアプリケーションから認識できるようにします。

## 2. 新しい検索条件の追加
GitHubリポジトリの検索フィルターを拡張する手順です。

1. **Schema定義**: `mb_scanner/lib/github/schema.py` の `SearchCriteria` クラスに新しいフィールドを追加します。
2. **クエリ変換**: `mb_scanner/lib/github/search.py` を修正し、追加した条件をGitHub APIのクエリ文字列に変換するロジックを実装します。
3. **CLI公開**: `mb_scanner/cli/search.py` の引数定義を更新し、ユーザーがCLIからその条件を指定できるようにします。

## 3. 新しい可視化の追加
分析結果のグラフやレポートを追加する手順です。

1. **プロット生成**: `mb_scanner/lib/visualization/` に新しいプロット生成モジュールを作成します（Matplotlib等を使用）。
2. **データ準備**: `mb_scanner/services/visualization_service.py` に、DBからデータを取得してプロット用に加工するロジックを追加します。
3. **コマンド追加**: `mb_scanner/cli/visualize.py` に新しいサブコマンドを追加して呼び出せるようにします。

## 4. データベーススキーマの変更
テーブル構造を変更する手順です。

1. **モデル変更**: `mb_scanner/models/` 内の該当モデルクラス定義を変更します。
2. **マイグレーション**: `mb_scanner/db/migrations.py` にマイグレーション処理（ALTER TABLE等）を追加します。
   - ※現状はAlembicを使用していないため、手動またはスクリプトによる更新が必要です。
3. **適用**: `mbs migrate` コマンドを実行して既存のデータベースを更新します。
