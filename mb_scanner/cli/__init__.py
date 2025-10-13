"""CLI パッケージの初期化とコマンド統合。

Typer アプリケーションを初期化し、各サブコマンド（search, codeql など）を統合します。
"""

from typer import Typer

from mb_scanner.cli.search import search_app

# メインの Typer アプリケーションを作成
app = Typer(help="MB-Scanner CLI - GitHub リポジトリ検索と保存ツール")

# search コマンドを追加
# 現在は search がデフォルトコマンドとして動作するよう、サブコマンドではなく直接統合
# これにより `mb-scanner search` と `mb-scanner` の両方が動作する
app.registered_commands.extend(search_app.registered_commands)
app.registered_groups.extend(search_app.registered_groups)

# 将来の拡張例（コメントアウト）:
# from mb_scanner.cli.codeql import codeql_app
# app.add_typer(codeql_app, name="codeql")


def main() -> None:
    """CLI のエントリーポイント。

    この関数は、pyproject.toml の [project.scripts] で指定されたエントリーポイントです。
    """
    app()


__all__ = ["app", "main"]
