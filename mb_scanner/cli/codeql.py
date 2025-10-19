"""CodeQL関連のCLIコマンドモジュール

このモジュールでは、CodeQLデータベース作成のためのCLIコマンドを提供します。
"""

import typer

from mb_scanner.core.config import settings
from mb_scanner.db.session import SessionLocal
from mb_scanner.lib.codeql import CodeQLCLI, CodeQLDatabaseManager
from mb_scanner.lib.github import RepositoryCloner
from mb_scanner.services.project_service import ProjectService
from mb_scanner.workflows.codeql_database_creation import CodeQLDatabaseCreationWorkflow

codeql_app = typer.Typer(help="CodeQLデータベース作成コマンド")


@codeql_app.command("create-db")
def create_database(
    project_name: str = typer.Argument(..., help="プロジェクト名（owner/repo形式）"),
    language: str = typer.Option(
        None,
        help="解析言語（指定しない場合は設定ファイルのデフォルト値を使用）",
    ),
    force: bool = typer.Option(False, "--force", "-f", help="既存DBを上書きする"),
) -> None:
    """指定したプロジェクトのCodeQL DBを作成する

    Examples:
        $ mb-scanner codeql create-db facebook/react
        $ mb-scanner codeql create-db facebook/react --language=javascript --force
    """
    # 言語のデフォルト値を適用
    if language is None:
        language = settings.codeql_default_language

    typer.echo(f"Creating CodeQL database for: {project_name}")
    typer.echo(f"Language: {language}")

    # データベースセッションを作成
    db = SessionLocal()

    try:
        # プロジェクトサービスからプロジェクト情報を取得
        project_service = ProjectService(db)
        project = project_service.get_project_by_full_name(project_name)

        if not project:
            typer.echo(f"Error: Project not found: {project_name}", err=True)
            raise typer.Exit(code=1)

        # ワークフローを初期化
        cloner = RepositoryCloner(github_token=settings.github_token)
        codeql_cli = CodeQLCLI(cli_path=settings.codeql_cli_path)
        db_manager = CodeQLDatabaseManager(
            cli=codeql_cli,
            base_dir=settings.effective_codeql_db_dir,
        )
        workflow = CodeQLDatabaseCreationWorkflow(
            cloner=cloner,
            db_manager=db_manager,
            clone_base_dir=settings.effective_codeql_clone_dir,
        )

        # DB作成を実行
        result = workflow.create_database_for_project(
            project_full_name=project.full_name,
            repository_url=project.url,
            language=language,
            skip_if_exists=not force,
            force=force,
        )

        # 結果を表示
        if result["status"] == "created":
            typer.echo(f"✓ Successfully created database: {result['db_path']}")
        elif result["status"] == "skipped":
            typer.echo(f"⊘ Database already exists: {result['db_path']}")
            typer.echo("  Use --force to overwrite")
        elif result["status"] == "error":
            typer.echo(f"✗ Error: {result['error']}", err=True)
            raise typer.Exit(code=1)

    finally:
        db.close()


@codeql_app.command("create-db-batch")
def create_database_batch(
    language: str = typer.Option(
        None,
        help="解析言語（指定しない場合は設定ファイルのデフォルト値を使用）",
    ),
    max_projects: int | None = typer.Option(None, help="最大プロジェクト数"),
    skip_existing: bool = typer.Option(True, help="既存DBをスキップする"),
    force: bool = typer.Option(False, "--force", "-f", help="既存DBを上書きする"),
) -> None:
    """DB上の全プロジェクトに対してCodeQL DBを一括作成する

    Examples:
        $ mb-scanner codeql create-db-batch
        $ mb-scanner codeql create-db-batch --language=javascript --max-projects=10
        $ mb-scanner codeql create-db-batch --force
    """
    # 言語のデフォルト値を適用
    if language is None:
        language = settings.codeql_default_language

    typer.echo("Starting batch CodeQL database creation")
    typer.echo(f"Language: {language}")
    typer.echo(f"Max projects: {max_projects or 'unlimited'}")
    typer.echo(f"Skip existing: {skip_existing}")

    # データベースセッションを作成
    db = SessionLocal()

    try:
        # プロジェクトサービスから全プロジェクトを取得
        project_service = ProjectService(db)
        projects = project_service.get_all_project_urls()

        if not projects:
            typer.echo("No projects found in database")
            return

        # max_projectsが指定されている場合は制限
        if max_projects is not None:
            projects = projects[:max_projects]

        typer.echo(f"Found {len(projects)} projects")

        # ワークフローを初期化
        cloner = RepositoryCloner(github_token=settings.github_token)
        codeql_cli = CodeQLCLI(cli_path=settings.codeql_cli_path)
        db_manager = CodeQLDatabaseManager(
            cli=codeql_cli,
            base_dir=settings.effective_codeql_db_dir,
        )
        workflow = CodeQLDatabaseCreationWorkflow(
            cloner=cloner,
            db_manager=db_manager,
            clone_base_dir=settings.effective_codeql_clone_dir,
        )

        # バッチ処理を実行
        stats = workflow.create_databases_batch(
            projects=projects,
            language=language,
            skip_if_exists=skip_existing and not force,
            force=force,
        )

        # 結果を表示
        typer.echo("\n=== Batch Creation Summary ===")
        typer.echo(f"Total: {stats['total']}")
        typer.echo(f"✓ Created: {stats['created']}")
        typer.echo(f"⊘ Skipped: {stats['skipped']}")
        typer.echo(f"✗ Failed: {stats['failed']}")

    finally:
        db.close()
