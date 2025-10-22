"""CodeQL関連のCLIコマンドモジュール

このモジュールでは、CodeQLデータベース作成およびクエリ実行のためのCLIコマンドを提供します。
"""

from pathlib import Path

import typer

from mb_scanner.core.config import settings
from mb_scanner.db.session import SessionLocal
from mb_scanner.lib.codeql import CodeQLCLI, CodeQLDatabaseManager
from mb_scanner.lib.codeql.analyzer import CodeQLResultAnalyzer
from mb_scanner.lib.github import RepositoryCloner
from mb_scanner.services.project_service import ProjectService
from mb_scanner.workflows.codeql_database_creation import CodeQLDatabaseCreationWorkflow
from mb_scanner.workflows.codeql_query_execution import CodeQLQueryExecutionWorkflow

codeql_app = typer.Typer(help="CodeQL関連コマンド")


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


@codeql_app.command("query")
def query(
    project_name: str = typer.Argument(..., help="プロジェクト名（owner/repo形式）"),
    query_files: list[Path] = typer.Option(..., "--query-files", "-q", help="クエリファイルのパス（複数指定可能）"),
    format: str = typer.Option(None, "--format", help="出力形式"),
    threads: int | None = typer.Option(None, "--threads", help="使用するスレッド数"),
    ram: int | None = typer.Option(None, "--ram", help="使用するRAM（MB）"),
) -> None:
    """指定したプロジェクトのCodeQLデータベースに対してクエリを実行する

    各クエリファイルごとに別々のSARIFファイルを出力します。
    出力先: outputs/queries/{query_name}/{project-name}.sarif

    Examples:
        $ mb-scanner codeql query facebook/react --query-files codeql/queries/id_10.ql
        $ mb-scanner codeql query facebook/react -q query1.ql -q query2.ql
    """
    # デフォルト値の適用
    if format is None:
        format = settings.codeql_default_output_format

    typer.echo(f"Executing CodeQL query for: {project_name}")
    typer.echo(f"Query files: {', '.join(str(q) for q in query_files)}")
    typer.echo(f"Output directory: {settings.effective_codeql_output_dir}")

    # ワークフローを初期化
    codeql_cli = CodeQLCLI(cli_path=settings.codeql_cli_path)
    db_manager = CodeQLDatabaseManager(
        cli=codeql_cli,
        base_dir=settings.effective_codeql_db_dir,
    )
    workflow = CodeQLQueryExecutionWorkflow(
        codeql_cli=codeql_cli,
        db_manager=db_manager,
    )

    # クエリを実行
    result = workflow.execute_query_for_project(
        project_full_name=project_name,
        query_files=query_files,
        output_base_dir=settings.effective_codeql_output_dir,
        format=format,
        threads=threads,
        ram=ram,
    )

    # 結果を表示
    if result["status"] == "success":
        typer.echo(f"✓ Successfully executed {len(result['results'])} queries")
        for query_result in result["results"]:
            typer.echo(f"  - {query_result['query_file']}: {query_result['result_count']} results")
            typer.echo(f"    Output: {query_result['output_path']}")
    elif result["status"] == "error":
        typer.echo(f"✗ Error: {result['error']}", err=True)
        raise typer.Exit(code=1)


@codeql_app.command("query-batch")
def query_batch(
    query_files: list[Path] = typer.Option(..., "--query-files", "-q", help="クエリファイルのパス（複数指定可能）"),
    max_projects: int | None = typer.Option(None, "--max-projects", help="最大プロジェクト数"),
    format: str = typer.Option(None, "--format", help="出力形式"),
    threads: int | None = typer.Option(None, "--threads", help="使用するスレッド数"),
    ram: int | None = typer.Option(None, "--ram", help="使用するRAM（MB）"),
) -> None:
    """データベース上の全プロジェクトに対してクエリを一括実行する

    Examples:
        $ mb-scanner codeql query-batch --query-files codeql/queries/id_10.ql
        $ mb-scanner codeql query-batch -q codeql/queries/id_10.ql --max-projects 10
        $ mb-scanner codeql query-batch -q query1.ql -q query2.ql
    """
    # デフォルト値の適用
    if format is None:
        format = settings.codeql_default_output_format

    typer.echo("Starting batch CodeQL query execution")
    typer.echo(f"Query files: {', '.join(str(q) for q in query_files)}")
    typer.echo(f"Max projects: {max_projects or 'unlimited'}")
    typer.echo(f"Output directory: {settings.effective_codeql_output_dir}")

    # データベースセッションを作成
    db = SessionLocal()

    try:
        # プロジェクトサービスから全プロジェクトを取得
        project_service = ProjectService(db)
        all_projects = project_service.get_all_projects()

        if not all_projects:
            typer.echo("No projects found in database")
            return

        # プロジェクト名のリストを作成
        project_names = [project.full_name for project in all_projects]

        # max_projectsが指定されている場合は制限
        if max_projects is not None:
            project_names = project_names[:max_projects]

        typer.echo(f"Found {len(project_names)} projects")

        # ワークフローを初期化
        codeql_cli = CodeQLCLI(cli_path=settings.codeql_cli_path)
        db_manager = CodeQLDatabaseManager(
            cli=codeql_cli,
            base_dir=settings.effective_codeql_db_dir,
        )
        workflow = CodeQLQueryExecutionWorkflow(
            codeql_cli=codeql_cli,
            db_manager=db_manager,
        )

        # バッチ処理を実行
        stats = workflow.execute_queries_batch(
            projects=project_names,
            query_files=query_files,
            output_base_dir=settings.effective_codeql_output_dir,
            format=format,
            threads=threads,
            ram=ram,
        )

        # 結果を表示
        typer.echo("\n=== Batch Execution Summary ===")
        typer.echo(f"Total: {stats['total']}")
        typer.echo(f"✓ Success: {stats['success']}")
        typer.echo(f"✗ Failed: {stats['failed']}")

    finally:
        db.close()


@codeql_app.command("summary")
def summary(
    query_id: str = typer.Argument(..., help="クエリID（例: id_10）"),
    threshold: int | None = typer.Option(None, "--threshold", "-t", help="閾値（この値以上の結果のみ含める）"),
    output_dir: Path | None = typer.Option(None, "--output-dir", help="出力先ディレクトリ"),
) -> None:
    """指定したクエリIDのサマリーJSONを生成する

    クエリディレクトリ内のSARIFファイルから結果を集計し、
    サマリーJSONファイルを生成します。

    出力先:
        - 閾値なし: outputs/queries/{query_id}/summary.json
        - 閾値あり: outputs/queries/{query_id}/limit_{threshold}_summary.json

    Examples:
        $ mb-scanner codeql summary id_10
        $ mb-scanner codeql summary id_10 --threshold 10
        $ mb-scanner codeql summary id_10 -t 10 --output-dir custom/output
    """
    # 出力ディレクトリのデフォルト値を適用
    if output_dir is None:
        output_dir = settings.effective_codeql_output_dir

    # クエリディレクトリのパスを構築
    query_dir = output_dir / query_id

    # ディレクトリの存在確認
    if not query_dir.exists():
        typer.echo(f"Error: Query directory does not exist: {query_dir}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Generating summary for query: {query_id}")
    if threshold is not None:
        typer.echo(f"Threshold: {threshold}")
    typer.echo(f"Query directory: {query_dir}")

    # 結果を集計
    analyzer = CodeQLResultAnalyzer()
    try:
        results = analyzer.generate_summary_from_directory(query_dir, threshold=threshold)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e

    # ファイル名を決定
    filename = f"limit_{threshold}_summary.json" if threshold is not None else "summary.json"

    output_path = query_dir / filename

    # サマリーを保存
    analyzer.save_summary_json(query_id, results, output_path, threshold=threshold)

    # 結果を表示
    typer.echo(f"✓ Successfully generated summary: {output_path}")
    typer.echo(f"Total projects: {len(results)}")
    if results:
        typer.echo("\nResults:")
        for project, count in sorted(results.items(), key=lambda x: x[1], reverse=True):
            typer.echo(f"  - {project}: {count} results")
