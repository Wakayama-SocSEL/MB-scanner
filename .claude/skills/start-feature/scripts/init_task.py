"""Task初期化スクリプト: 連番付きディレクトリとテンプレートファイルを作成する."""

from pathlib import Path
import sys


def init_task(feature_name: str):
    """.ai/tasks/配下に連番付きディレクトリを作成し、plan.md/prompt.mdを初期化する

    Usage: python scripts/init_task.py <feature_name>
    """
    base_dir = Path(".ai/tasks")
    base_dir.mkdir(parents=True, exist_ok=True)

    # 既存の最大連番を取得
    existing_dirs = list(base_dir.glob("[0-9]*_*"))
    max_num = 0
    for d in existing_dirs:
        try:
            num_part = d.name.split("_")
            max_num = max(max_num, int(num_part[0]))
        except ValueError:
            continue

    # 新しいディレクトリ名を作成
    next_num = max_num + 1
    dir_name = f"{next_num:04d}_{feature_name}"
    task_dir = base_dir / dir_name
    task_dir.mkdir()

    # plan.md の作成
    plan_path = task_dir / "plan.md"
    with Path.open(plan_path, "w") as f:
        f.write(f"# Implementation Plan: {feature_name}\n\n## 目的\n\n## 変更計画\n\n## 影響範囲\n")

    # prompt.md の作成
    prompt_path = task_dir / "prompt.md"
    with Path.open(prompt_path, "w") as f:
        f.write(f"# Task Context: {feature_name}\n\n## ユーザー要望\n\n## 対応履歴\n")

    print(f"SUCCESS: Created task directory: {task_dir}")
    print(f"Please edit: {plan_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python init_task.py <feature_name>")
        sys.exit(1)
    init_task(sys.argv[1])
