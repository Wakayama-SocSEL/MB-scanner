"""CLI パッケージの初期化とコマンド統合。

Typer アプリケーションを初期化し、各サブコマンド（search, codeql など）を統合します。
"""

from typer import Typer

from mb_scanner.cli.codeql import codeql_app
from mb_scanner.cli.count_lines import count_lines_app
from mb_scanner.cli.github import github_app
from mb_scanner.cli.migrate import migrate_app
from mb_scanner.cli.search import search_app
from mb_scanner.cli.visualize import visualize_app

# メインの Typer アプリケーションを作成
app = Typer(help="MB-Scanner CLI - GitHub リポジトリ検索と保存ツール")

# search コマンドを追加
# 現在は search がデフォルトコマンドとして動作するよう、サブコマンドではなく直接統合
# これにより `mb-scanner search` と `mb-scanner` の両方が動作する
app.registered_commands.extend(search_app.registered_commands)
app.registered_groups.extend(search_app.registered_groups)

# codeql コマンドを追加
app.add_typer(codeql_app, name="codeql")

# github コマンドを追加
app.add_typer(github_app, name="github")

# count-lines コマンドを追加
app.registered_commands.extend(count_lines_app.registered_commands)
app.registered_groups.extend(count_lines_app.registered_groups)

# migrate コマンドを追加
app.registered_commands.extend(migrate_app.registered_commands)
app.registered_groups.extend(migrate_app.registered_groups)

# visualize コマンドを追加
app.add_typer(visualize_app, name="visualize")


def main() -> None:
    """CLI のエントリーポイント。

    この関数は、pyproject.toml の [project.scripts] で指定されたエントリーポイントです。
    """
    app()


__all__ = ["app", "main"]
