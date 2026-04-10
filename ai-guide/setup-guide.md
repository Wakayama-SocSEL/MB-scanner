# 開発環境セットアップガイド

## 技術スタック

| ツール | 用途 | コマンド例 |
| :--- | :--- | :--- |
| **uv** | 高速パッケージ管理 | `uv sync`, `uv add`, `uv run` |
| **just** | タスクランナー | `just fix`, `just typecheck` |
| **Python** | ランタイム | 3.13+ |
| **CodeQL** | 解析エンジン | `codeql database create` |

## 重要なルール

- **パッケージ管理**: 必ず `uv` を使用すること。`pip` や `poetry` は使用禁止。
  - 追加: `uv add <package>`
  - 開発用追加: `uv add --dev <package>`
  - 同期: `uv sync`
- **タスクランナー**: コマンド実行には `just` を使用すること（例: `just fix`, `just typecheck`）。

## 初回セットアップ / 環境リセット

1. `.env` ファイルが存在するか確認し、なければ `.env.sample` からコピーして作成する。
   ```bash
   cp .env.sample .env
   ```
2. `.env` を開き、`GITHUB_TOKEN`（scope: `public_repo`）を設定する。
3. `uv sync` を実行して依存関係をインストールする。

## アプリケーション実行

```bash
uv run mbs <subcommand>   # mbs はエイリアス
```

## トラブルシューティング

- **ImportError**: `uv run` を先頭につけてコマンドを実行する。
- **DBエラー**: `rm mb_scanner.db` でローカルDBを削除し、`uv run mbs migrate` で再作成する。
- **CLIコマンドが認識されない**: `uv pip install -e .` で編集可能モードで再インストールする。
