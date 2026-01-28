"""ベンチマークデータ抽出CLIコマンド

JSONLファイルからslow/fastコードを読み込み、個別ファイルに展開します。
"""

from pathlib import Path

import typer

from mb_scanner.models.benchmark import BenchmarkEntry

benchmark_app = typer.Typer(help="Benchmark data commands")


@benchmark_app.command("extract")
def extract(
    input_file: Path = typer.Argument(
        ...,
        help="入力JSONLファイルのパス",
    ),
    id_filter: int | None = typer.Option(
        None,
        "--id",
        help="特定のIDのみ抽出",
    ),
    ids_filter: str | None = typer.Option(
        None,
        "--ids",
        help="カンマ区切りで複数ID指定 (例: 0,1,2,3)",
    ),
    count: int | None = typer.Option(
        None,
        "--count",
        help="抽出する件数",
    ),
    offset: int = typer.Option(
        0,
        "--offset",
        help="開始位置（0始まり）",
    ),
    output_dir: Path | None = typer.Option(
        None,
        "--output-dir",
        help="出力先ディレクトリ（デフォルト: 入力ファイルと同じディレクトリ）",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="既存ファイルを上書き",
    ),
) -> None:
    """JSONLファイルからslow/fastコードを個別ファイルに展開する

    各エントリは id_{id}/slow.js と id_{id}/fast.js として出力されます。
    """
    if not input_file.exists():
        typer.echo(typer.style(f"Error: Input file not found: {input_file}", fg=typer.colors.RED), err=True)
        raise typer.Exit(code=1)

    # 出力先ディレクトリの決定
    dest_dir = output_dir or input_file.parent

    # ID フィルタの解析
    target_ids: set[int] | None = None
    if id_filter is not None:
        target_ids = {id_filter}
    elif ids_filter is not None:
        target_ids = {int(id_str.strip()) for id_str in ids_filter.split(",")}

    # JSONLファイルの読み込みとフィルタリング
    entries: list[BenchmarkEntry] = []
    with input_file.open("r", encoding="utf-8") as f:
        for line_num, raw_line in enumerate(f):
            stripped = raw_line.strip()
            if not stripped:
                continue

            # offset適用
            if line_num < offset:
                continue

            entry = BenchmarkEntry.model_validate_json(stripped)

            # IDフィルタ適用
            if target_ids is not None and entry.id not in target_ids:
                continue

            entries.append(entry)

            # count制限
            if count is not None and len(entries) >= count:
                break

    # ファイル展開
    created = 0
    skipped = 0

    for entry in entries:
        entry_dir = dest_dir / f"id_{entry.id}"

        if entry_dir.exists() and not force:
            skipped += 1
            continue

        entry_dir.mkdir(parents=True, exist_ok=True)
        (entry_dir / "slow.js").write_text(entry.slow, encoding="utf-8")
        (entry_dir / "fast.js").write_text(entry.fast, encoding="utf-8")
        created += 1

    total = created + skipped
    typer.echo(f"Total: {total} | Created: {created} | Skipped: {skipped}")


if __name__ == "__main__":
    benchmark_app()
