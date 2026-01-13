"""可視化コマンドのCLI実装"""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import typer

from mb_scanner.core.config import settings
from mb_scanner.lib.visualization.boxplot import create_boxplot_summary
from mb_scanner.lib.visualization.scatter_plot import create_hexbin_plot, create_scatter_plot
from mb_scanner.services.visualization_service import VisualizationService

visualize_app = typer.Typer(help="Visualization commands")


@visualize_app.command("scatter")
def scatter(
    query_result: Path = typer.Option(
        ...,
        "--query-result",
        "-q",
        help="Path to query result JSON file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output: Path = typer.Option(
        "outputs/plots/scatter.png",
        "--output",
        "-o",
        help="Output path for the scatter plot",
    ),
    title: str = typer.Option(
        "CodeQL Detection vs JS Lines",
        "--title",
        "-t",
        help="Title for the scatter plot",
    ),
    xlabel: str = typer.Option(
        "JavaScript Lines Count",
        "--xlabel",
        help="X-axis label",
    ),
    ylabel: str = typer.Option(
        "Detection Count",
        "--ylabel",
        help="Y-axis label",
    ),
    log_scale_x: bool = typer.Option(
        False,
        "--log-scale-x/--no-log-scale-x",
        help="Use logarithmic scale for x-axis",
    ),
    log_scale_y: bool = typer.Option(
        False,
        "--log-scale-y/--no-log-scale-y",
        help="Use logarithmic scale for y-axis",
    ),
    show_correlation: bool = typer.Option(
        False,
        "--show-correlation/--no-show-correlation",
        help="Show Spearman's rank correlation coefficient on the plot",
    ),
    show_regression: bool = typer.Option(
        False,
        "--show-regression/--no-show-regression",
        help="Show linear regression line on the plot",
    ),
    use_hexbin: bool = typer.Option(
        False,
        "--use-hexbin/--no-use-hexbin",
        help="Use hexbin plot instead of scatter plot",
    ),
    gridsize: int = typer.Option(
        20,
        "--gridsize",
        help="Grid size for hexbin plot (only used with --use-hexbin)",
    ),
    cmap: str = typer.Option(
        "YlOrRd",
        "--cmap",
        help="Colormap for hexbin plot (only used with --use-hexbin)",
    ),
) -> None:
    r"""Create scatter plot for CodeQL results vs JS lines count

    This command reads CodeQL query results from a JSON file,
    retrieves corresponding project data from the database,
    and generates a scatter plot visualization.

    Example:
        mb-scanner visualize scatter \
            --query-result outputs/queries/detect_strict/limit_1_summary.json \
            --output outputs/plots/scatter_id_222.png
    """
    try:
        # データベース接続
        engine = create_engine(settings.database_url)
        session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = session_local()

        try:
            # VisualizationServiceでデータ取得
            vis_service = VisualizationService(db)
            typer.echo(f"Loading query results from: {query_result}")
            scatter_data = vis_service.get_scatter_data(query_result)

            if not scatter_data:
                typer.echo(
                    typer.style(
                        "Warning: No data points found. Check if projects exist in DB and have js_lines_count.",
                        fg=typer.colors.YELLOW,
                    )
                )

            # 散布図またはhexbinプロットを生成
            if use_hexbin:
                typer.echo(f"Creating hexbin plot with {len(scatter_data)} data points...")
                create_hexbin_plot(
                    scatter_data,
                    output,
                    title=title,
                    xlabel=xlabel,
                    ylabel=ylabel,
                    log_scale_x=log_scale_x,
                    log_scale_y=log_scale_y,
                    gridsize=gridsize,
                    cmap=cmap,
                    show_correlation=show_correlation,
                    show_regression=show_regression,
                )
                typer.echo(typer.style(f"✓ Hexbin plot saved to: {output}", fg=typer.colors.GREEN, bold=True))
            else:
                typer.echo(f"Creating scatter plot with {len(scatter_data)} data points...")
                create_scatter_plot(
                    scatter_data,
                    output,
                    title=title,
                    xlabel=xlabel,
                    ylabel=ylabel,
                    log_scale_x=log_scale_x,
                    log_scale_y=log_scale_y,
                    show_correlation=show_correlation,
                    show_regression=show_regression,
                )
                typer.echo(typer.style(f"✓ Scatter plot saved to: {output}", fg=typer.colors.GREEN, bold=True))

        finally:
            db.close()

    except FileNotFoundError as e:
        typer.echo(typer.style(f"Error: {e}", fg=typer.colors.RED), err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(typer.style(f"Error: {e}", fg=typer.colors.RED), err=True)
        raise typer.Exit(code=1) from e


@visualize_app.command("boxplot")
def boxplot(
    input_dir: Path = typer.Option(
        ...,
        "--input-dir",
        "-i",
        help="Directory containing summary JSON files",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
    ),
    output: Path = typer.Option(
        "outputs/plots/boxplot_summary.png",
        "--output",
        "-o",
        help="Output path for the boxplot",
    ),
    title: str = typer.Option(
        "CodeQL Query Results - Box Plot Summary",
        "--title",
        "-t",
        help="Title for the boxplot",
    ),
    log_scale: bool = typer.Option(
        False,
        "--log-scale/--no-log-scale",
        help="Use logarithmic scale for y-axis",
    ),
    query_order: str = typer.Option(
        "",
        "--query-order",
        help="Comma-separated list of query IDs to specify display order (e.g., 'id_10,id_18,id_222')",
    ),
) -> None:
    r"""Create boxplot summary for multiple CodeQL query results

    This command reads multiple summary JSON files from a directory
    and generates a boxplot visualization comparing the results.

    Example:
        # Linear scale (default)
        mb-scanner visualize boxplot \
            --input-dir outputs/queries/detect_strict/summary \
            --output outputs/plots/boxplot_summary.png

        # Logarithmic scale
        mb-scanner visualize boxplot \
            --input-dir outputs/queries/detect_strict/summary \
            --output outputs/plots/boxplot_summary.png \
            --log-scale
    """
    try:
        typer.echo(f"Loading summary data from: {input_dir}")
        typer.echo(f"Y-axis scale: {'logarithmic' if log_scale else 'linear'}")

        # query_orderを解析
        query_order_list: list[str] | None = None
        if query_order:
            query_order_list = [q.strip() for q in query_order.split(",") if q.strip()]
            typer.echo(f"Query order: {', '.join(query_order_list)}")

        # 箱ひげ図を生成
        create_boxplot_summary(
            input_dir,
            output,
            log_scale=log_scale,
            title=title,
            query_order=query_order_list,
        )

        typer.echo(typer.style(f"✓ Boxplot saved to: {output}", fg=typer.colors.GREEN, bold=True))

    except ValueError as e:
        typer.echo(typer.style(f"Error: {e}", fg=typer.colors.RED), err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(typer.style(f"Error: {e}", fg=typer.colors.RED), err=True)
        raise typer.Exit(code=1) from e


if __name__ == "__main__":
    visualize_app()
