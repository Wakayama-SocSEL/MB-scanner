"""コンテキスト収集スクリプト: タスクディレクトリからplan.mdとprompt.mdを取得する."""

from pathlib import Path
import sys


def collect_context(target: str | None = None):
    """.ai/tasks/ 配下の plan.md と prompt.md を取得して表示する

    target: 連番(int) または 機能名(str)。Noneの場合は最新のタスク。
    """
    base_dir = Path(".ai/tasks")
    if not base_dir.exists():
        print("Error: .ai/tasks directory not found.")
        sys.exit(1)

    # タスクディレクトリのリスト取得
    task_dirs = sorted(base_dir.glob("*_*"))
    if not task_dirs:
        print("No tasks found.")
        sys.exit(1)

    selected_dir = None

    if target is None:
        # 最新を取得
        selected_dir = task_dirs[-1]
    else:
        # ターゲット検索
        for d in task_dirs:
            if target in d.name:  # 連番や名前の部分一致
                selected_dir = d
                break

    if not selected_dir:
        print(f"Task matching '{target}' not found.")
        sys.exit(1)

    print(f"--- Context from: {selected_dir.name} ---")

    # ファイル読み込み
    for filename in ["plan.md", "prompt.md"]:
        file_path = selected_dir / filename
        if file_path.exists():
            print(f"\n# File: {filename}\n")
            print(file_path.read_text(encoding="utf-8"))
        else:
            print(f"\n# File: {filename} (Not found)\n")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    collect_context(target)
