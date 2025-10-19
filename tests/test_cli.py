"""CLI コマンドのテスト"""

from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from mb_scanner.cli import app


@pytest.fixture
def runner():
    """Typer の CliRunner を提供するフィクスチャ"""
    return CliRunner()


@pytest.fixture
def mock_workflow_stats():
    """ワークフロー実行結果のモックデータ"""
    return {
        "total": 10,
        "saved": 8,
        "updated": 1,
        "skipped": 1,
        "failed": 0,
    }


def test_search_command_with_defaults(runner, mock_workflow_stats):
    """デフォルトオプションで search コマンドが実行できることを確認する"""
    with (
        patch("mb_scanner.cli.search.init_db") as mock_init_db,
        patch("mb_scanner.cli.search.get_db") as mock_get_db,
        patch("mb_scanner.cli.search.SearchAndStoreWorkflow") as mock_workflow_class,
    ):
        # モックの設定
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])

        mock_workflow = Mock()
        mock_workflow.execute.return_value = mock_workflow_stats
        mock_workflow_class.return_value = mock_workflow

        # コマンドを実行（searchコマンドを明示的に指定）
        result = runner.invoke(app, ["search"])

        # 検証
        assert result.exit_code == 0
        mock_init_db.assert_called_once()
        mock_workflow.execute.assert_called_once()
        assert "検索結果総数: 10" in result.stdout
        assert "新規保存: 8" in result.stdout
        assert "完了しました" in result.stdout


def test_search_command_with_custom_options(runner, mock_workflow_stats):
    """カスタムオプションで search コマンドが実行できることを確認する"""
    with (
        patch("mb_scanner.cli.search.init_db") as mock_init_db,
        patch("mb_scanner.cli.search.get_db") as mock_get_db,
        patch("mb_scanner.cli.search.SearchAndStoreWorkflow") as mock_workflow_class,
    ):
        # モックの設定
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])

        mock_workflow = Mock()
        mock_workflow.execute.return_value = mock_workflow_stats
        mock_workflow_class.return_value = mock_workflow

        # コマンドを実行
        result = runner.invoke(
            app,
            [
                "search",
                "--language",
                "Python",
                "--min-stars",
                "1000",
                "--max-days-since-commit",
                "180",
                "--max-results",
                "50",
                "--update",
            ],
        )

        # 検証
        assert result.exit_code == 0
        mock_init_db.assert_called_once()

        # execute が正しい引数で呼ばれたか確認
        call_args = mock_workflow.execute.call_args
        assert call_args is not None
        criteria = call_args.kwargs["criteria"]
        assert criteria.language == "Python"
        assert criteria.min_stars == 1000
        assert criteria.max_days_since_commit == 180
        assert call_args.kwargs["max_results"] == 50
        assert call_args.kwargs["update_if_exists"] is True

        # 出力の確認
        assert "言語: Python" in result.stdout
        assert "最小スター数: 1000" in result.stdout
        assert "最終コミット経過日数: 180日以内" in result.stdout
        assert "最大取得数: 50" in result.stdout
        assert "既存プロジェクトの更新: 有効" in result.stdout


def test_search_command_with_short_options(runner, mock_workflow_stats):
    """短縮オプションで search コマンドが実行できることを確認する"""
    with (
        patch("mb_scanner.cli.search.init_db"),
        patch("mb_scanner.cli.search.get_db") as mock_get_db,
        patch("mb_scanner.cli.search.SearchAndStoreWorkflow") as mock_workflow_class,
    ):
        # モックの設定
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])

        mock_workflow = Mock()
        mock_workflow.execute.return_value = mock_workflow_stats
        mock_workflow_class.return_value = mock_workflow

        # コマンドを実行（短縮オプション使用）
        result = runner.invoke(
            app,
            [
                "search",
                "-l",
                "TypeScript",
                "-s",
                "500",
                "-d",
                "90",
                "-n",
                "25",
                "-u",
            ],
        )

        # 検証
        assert result.exit_code == 0

        # execute が正しい引数で呼ばれたか確認
        call_args = mock_workflow.execute.call_args
        assert call_args is not None
        criteria = call_args.kwargs["criteria"]
        assert criteria.language == "TypeScript"
        assert criteria.min_stars == 500
        assert criteria.max_days_since_commit == 90
        assert call_args.kwargs["max_results"] == 25
        assert call_args.kwargs["update_if_exists"] is True


def test_search_command_with_failures(runner):
    """一部失敗したケースで警告メッセージが表示されることを確認する"""
    stats_with_failures = {
        "total": 10,
        "saved": 7,
        "updated": 0,
        "skipped": 0,
        "failed": 3,
    }

    with (
        patch("mb_scanner.cli.search.init_db"),
        patch("mb_scanner.cli.search.get_db") as mock_get_db,
        patch("mb_scanner.cli.search.SearchAndStoreWorkflow") as mock_workflow_class,
    ):
        # モックの設定
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])

        mock_workflow = Mock()
        mock_workflow.execute.return_value = stats_with_failures
        mock_workflow_class.return_value = mock_workflow

        # コマンドを実行
        result = runner.invoke(app, ["search"])

        # 検証
        assert result.exit_code == 0
        assert "失敗: 3" in result.stdout
        assert "警告: 一部のリポジトリの保存に失敗しました" in result.stdout


def test_search_command_with_exception(runner):
    """例外が発生した場合にエラーメッセージが表示されることを確認する"""
    with (
        patch("mb_scanner.cli.search.init_db"),
        patch("mb_scanner.cli.search.get_db") as mock_get_db,
        patch("mb_scanner.cli.search.SearchAndStoreWorkflow") as mock_workflow_class,
    ):
        # モックの設定
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])

        mock_workflow = Mock()
        mock_workflow.execute.side_effect = Exception("GitHub API error")
        mock_workflow_class.return_value = mock_workflow

        # コマンドを実行
        result = runner.invoke(app, ["search"])

        # 検証
        assert result.exit_code == 1
        # エラーメッセージは stderr に出力される
        assert "エラーが発生しました" in result.stderr or "エラーが発生しました" in result.output


def test_search_command_workflow_cleanup(runner, mock_workflow_stats):
    """ワークフローが正しくクローズされることを確認する"""
    with (
        patch("mb_scanner.cli.search.init_db"),
        patch("mb_scanner.cli.search.get_db") as mock_get_db,
        patch("mb_scanner.cli.search.SearchAndStoreWorkflow") as mock_workflow_class,
    ):
        # モックの設定
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])

        mock_workflow = Mock()
        mock_workflow.execute.return_value = mock_workflow_stats
        mock_workflow_class.return_value = mock_workflow

        # コマンドを実行
        result = runner.invoke(app, ["search"])

        # 検証
        assert result.exit_code == 0
        mock_workflow.close.assert_called_once()
        mock_db.close.assert_called_once()


def test_search_command_cleanup_on_exception(runner):
    """例外が発生した場合でもクリーンアップされることを確認する"""
    with (
        patch("mb_scanner.cli.search.init_db"),
        patch("mb_scanner.cli.search.get_db") as mock_get_db,
        patch("mb_scanner.cli.search.SearchAndStoreWorkflow") as mock_workflow_class,
    ):
        # モックの設定
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])

        mock_workflow = Mock()
        mock_workflow.execute.side_effect = Exception("Test exception")
        mock_workflow_class.return_value = mock_workflow

        # コマンドを実行
        result = runner.invoke(app, ["search"])

        # 検証
        assert result.exit_code == 1
        # 例外が発生してもデータベースはクローズされるべき
        mock_db.close.assert_called_once()


def test_search_command_invalid_min_stars(runner):
    """無効な最小スター数（負の値）が拒否されることを確認する"""
    result = runner.invoke(app, ["search", "--min-stars", "-10"])

    # 検証
    assert result.exit_code != 0
    # stderr も確認（Typer は stderr にエラーを出力する）
    output = result.stdout + (result.stderr if hasattr(result, "stderr") else "")
    assert "Invalid value" in output or "Error" in output or "error" in output.lower()


def test_search_command_invalid_max_days(runner):
    """無効な最大日数（0以下）が拒否されることを確認する"""
    result = runner.invoke(app, ["search", "--max-days-since-commit", "0"])

    # 検証
    assert result.exit_code != 0
    # stderr も確認（Typer は stderr にエラーを出力する）
    output = result.stdout + (result.stderr if hasattr(result, "stderr") else "")
    assert "Invalid value" in output or "Error" in output or "error" in output.lower()
