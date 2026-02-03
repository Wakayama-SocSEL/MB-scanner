# 開発環境セットアップガイド

## 技術スタック (前提条件)
本プロジェクトでは以下の最新ツールチェーンを使用しています。古い手法（requirements.txtなど）は使用しません。

| ツール | 用途 | コマンド例 |
| :--- | :--- | :--- |
| **uv** | 高速パッケージ管理 | `uv sync`, `uv add`, `uv run` |
| **just** | タスクランナー | `just fix`, `just test` |
| **Python** | ランタイム | 3.13+ |
| **CodeQL** | 解析エンジン | `codeql database create` |

## 環境変数設定 (.env)
GitHub API 連携のために `.env` ファイルの設定が必須です。

### 必須変数
- `GITHUB_TOKEN`: GitHub Personal Access Token (scope: `public_repo`)
  - 取得先: GitHub Settings > Developer settings > Personal access tokens

### 設定手順
1. プロジェクトルートの `.env.sample` を `.env` にコピーする。
   ```bash
   cp .env.sample .env
   ```
2. .env を開き、実際のトークン値を設定する。

## コマンドリファレンス

### 依存関係の管理
- インストール/同期: uv sync
- パッケージ追加: uv add <package_name>
- 開発用パッケージ追加: uv add --dev <package_name>

### アプリケーション実行
- CLI実行: uv run mbs <subcommand> (または uv run mb-scanner)
    - エイリアス: mbs コマンドが定義されています。

### 開発支援 (Justfile)
- コード整形・Lint修正: just fix (ruff check --fix && ruff format)
- 型チェック: just typecheck (pyright)
- テスト実行: uv run pytest

## トラブルシューティング
- ImportErrorが出る場合: 仮想環境が有効になっていない可能性があります。uv run を頭につけてコマンドを実行してください。
- DBエラー: rm mb_scanner.db でローカルDBを削除し、uv run mbs migrate で再作成してください。
- **CLIコマンド (mbs/mb-scanner) が認識されない場合**:
  `uv sync` 後もコマンドが使えない、あるいはコードの変更が反映されない場合は、以下のコマンドでパッケージを編集可能モード（Editable Mode）で再インストールしてください。
  ```bash
  uv pip install -e .
  ```
