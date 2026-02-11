"""ベンチマークデータ抽出CLIコマンド

JSONLファイルからslow/fastコードを読み込み、個別ファイルに展開します。
等価性チェック機能も提供します。
"""

import json
from pathlib import Path
import re
from typing import Any

import typer

from mb_scanner.models.benchmark import BenchmarkEntry
from mb_scanner.services.benchmark_runner import run_batch_equivalence_check

benchmark_app = typer.Typer(help="Benchmark data commands")


def compact_json_array(json_str: str) -> str:
    """配列のみをコンパクト表示に変換する

    JSONの配列部分を1行にまとめて表示します。
    オブジェクトの構造は維持されます。

    Args:
        json_str: 整形されたJSON文字列

    Returns:
        配列をコンパクト表示したJSON文字列
    """

    # 配列部分を検出して1行にまとめる正規表現パターン
    # 改行とインデントを含む配列を検出: [\n  "item1",\n  "item2"\n]
    def compact_array(match: re.Match[str]) -> str:
        array_content = match.group(0)
        # 配列内の改行とインデントを削除
        compact = re.sub(r"\n\s*", "", array_content)
        # カンマの後にスペースを1つ追加
        compact = re.sub(r",(?=\S)", ", ", compact)
        return compact

    # 配列パターン: [ で始まり ] で終わる
    # (?s) は . を改行にもマッチさせるフラグ
    pattern = r'\[(?:\s*"[^"]*"(?:\s*,\s*"[^"]*")*\s*|\s*\d+(?:\s*,\s*\d+)*\s*|\s*(?:"[^"]*"|\d+|\{[^}]*\})(?:\s*,\s*(?:"[^"]*"|\d+|\{[^}]*\}))*\s*)\]'

    # より汎用的なパターン: 配列全体を検出
    pattern = r"\[\s*(?:[^\[\]]*)\s*\]"

    # 再帰的に処理するため、内側の配列から順に処理
    max_iterations = 10
    for _ in range(max_iterations):
        new_str = re.sub(pattern, compact_array, json_str)
        if new_str == json_str:
            break
        json_str = new_str

    return json_str


def format_json_compact_arrays(data: dict[str, Any]) -> str:
    """配列をコンパクト表示したJSON文字列を生成する

    Args:
        data: JSONにシリアライズするデータ

    Returns:
        配列をコンパクト表示したJSON文字列
    """
    # まず標準的なインデント付きJSON文字列を生成
    json_str = json.dumps(data, indent=2, ensure_ascii=False)

    # 配列部分をコンパクトに変換
    return compact_json_array(json_str)


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


@benchmark_app.command("equivalence-check")
def equivalence_check(
    input_dir: Path = typer.Argument(
        ...,
        help="id_* ディレクトリを含む親ディレクトリのパス",
    ),
    id_filter: int | None = typer.Option(
        None,
        "--id",
        help="特定のIDのみチェック",
    ),
    ids_filter: str | None = typer.Option(
        None,
        "--ids",
        help="カンマ区切りで複数ID指定 (例: 0,1,2,3)",
    ),
    count: int | None = typer.Option(
        None,
        "--count",
        help="チェックする件数",
    ),
    offset: int = typer.Option(
        0,
        "--offset",
        help="開始位置（0始まり）",
    ),
    timeout: int = typer.Option(
        100,
        "--timeout",
        help="1件あたりのタイムアウト（秒）",
    ),
    workers: int = typer.Option(
        4,
        "--workers",
        help="並列ワーカー数",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="結果JSONファイルの出力先",
    ),
) -> None:
    """slow/fastコードの実行結果が等価かを検証する

    extractで展開したディレクトリを対象に、各エントリの
    slow.jsとfast.jsの実行結果を比較します。
    """
    if not input_dir.exists():
        typer.echo(
            typer.style(f"Error: Directory not found: {input_dir}", fg=typer.colors.RED),
            err=True,
        )
        raise typer.Exit(code=1)

    # IDフィルタの解析
    target_ids: set[int] | None = None
    if id_filter is not None:
        target_ids = {id_filter}
    elif ids_filter is not None:
        target_ids = {int(id_str.strip()) for id_str in ids_filter.split(",")}

    typer.echo(f"Running equivalence check on {input_dir} ...")

    summary = run_batch_equivalence_check(
        input_dir=input_dir,
        target_ids=target_ids,
        count=count,
        offset=offset,
        timeout=timeout,
        workers=workers,
    )

    # 結果表示
    typer.echo(
        f"Total: {summary.total} | Equal: {summary.equal} | Not Equal: {summary.not_equal} "
        f"| Error: {summary.error} | Timeout: {summary.timeout} | Skipped: {summary.skipped}"
    )

    # JSON出力
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        # 配列をコンパクト表示したJSON文字列を生成
        json_str = format_json_compact_arrays(summary.model_dump())
        output.write_text(json_str, encoding="utf-8")
        typer.echo(f"Results saved to {output}")


if __name__ == "__main__":
    benchmark_app()
