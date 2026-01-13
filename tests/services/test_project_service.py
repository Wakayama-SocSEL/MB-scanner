"""ProjectService のテスト

このモジュールでは、ProjectService の全機能をテストします。
特に topics との連携が正しく動作することを重点的に確認します。
"""

from datetime import datetime

import pytest

from mb_scanner.services.project_service import ProjectService


def test_save_project_new(project_service: ProjectService) -> None:
    """新規プロジェクト保存のテスト

    新しいプロジェクトが正しく保存されることを確認します。
    """
    # 実行
    project = project_service.save_project(
        full_name="facebook/react",
        url="https://github.com/facebook/react",
        stars=250000,
        language="JavaScript",
        description="A JavaScript library for building user interfaces",
        last_commit_date=datetime(2025, 10, 1),
    )

    # 検証
    assert project.id is not None
    assert project.full_name == "facebook/react"
    assert project.url == "https://github.com/facebook/react"
    assert project.stars == 250000
    assert project.language == "JavaScript"
    assert project.fetched_at is not None

    # DBから取得して確認
    saved_project = project_service.get_project_by_full_name("facebook/react")
    assert saved_project is not None
    assert saved_project.full_name == "facebook/react"


def test_save_project_duplicate_skip(project_service: ProjectService) -> None:
    """重複プロジェクトのスキップテスト

    同じfull_nameのプロジェクトを保存しようとした場合、
    update_if_exists=False（デフォルト）なら既存のものが返されることを確認します。
    """
    # 事前準備: 最初のプロジェクトを保存
    first_project = project_service.save_project(
        full_name="facebook/react",
        url="https://github.com/facebook/react",
        stars=250000,
        language="JavaScript",
        description="First description",
        last_commit_date=datetime(2025, 10, 1),
    )
    first_id = first_project.id
    first_stars = first_project.stars

    # 実行: 同じfull_nameで異なるデータを保存しようとする
    second_project = project_service.save_project(
        full_name="facebook/react",
        url="https://github.com/facebook/react",
        stars=300000,  # 異なる値
        language="JavaScript",
        description="Second description",  # 異なる値
        last_commit_date=datetime(2025, 10, 2),
    )

    # 検証: 既存のプロジェクトが返される（更新されていない）
    assert second_project.id == first_id
    assert second_project.stars == first_stars  # 250000（元の値）
    assert second_project.description == "First description"  # 元の値

    # DBには1件のみ存在
    all_projects = project_service.get_all_projects()
    assert len(all_projects) == 1


def test_save_project_update_if_exists(project_service: ProjectService) -> None:
    """update_if_exists=True での更新テスト

    update_if_exists=True の場合、既存プロジェクトが更新されることを確認します。
    """
    # 事前準備: 最初のプロジェクトを保存
    first_project = project_service.save_project(
        full_name="facebook/react",
        url="https://github.com/facebook/react",
        stars=250000,
        language="JavaScript",
        description="Old description",
        last_commit_date=datetime(2025, 10, 1),
    )
    first_id = first_project.id

    # 実行: update_if_exists=True で更新
    updated_project = project_service.save_project(
        full_name="facebook/react",
        url="https://github.com/facebook/react-new",  # 変更
        stars=300000,  # 変更
        language="TypeScript",  # 変更
        description="New description",  # 変更
        last_commit_date=datetime(2025, 10, 2),  # 変更
        update_if_exists=True,
    )

    # 検証: IDは同じだが、内容が更新されている
    assert updated_project.id == first_id
    assert updated_project.url == "https://github.com/facebook/react-new"
    assert updated_project.stars == 300000
    assert updated_project.language == "TypeScript"
    assert updated_project.description == "New description"

    # DBには1件のみ存在
    all_projects = project_service.get_all_projects()
    assert len(all_projects) == 1


def test_save_project_with_topics(project_service: ProjectService) -> None:
    """topics付きプロジェクト保存のテスト

    topicsを指定してプロジェクトを保存した場合、
    topicが正しく関連付けられることを確認します。
    """
    # 実行
    project = project_service.save_project(
        full_name="facebook/react",
        url="https://github.com/facebook/react",
        stars=250000,
        language="JavaScript",
        description="A JavaScript library",
        last_commit_date=datetime(2025, 10, 1),
        topics=["react", "javascript", "frontend"],
    )

    # 検証: topicsが関連付けられている
    assert len(project.topics) == 3
    topic_names = {topic.name for topic in project.topics}
    assert topic_names == {"react", "javascript", "frontend"}

    # DBから取得して確認
    saved_project = project_service.get_project_by_full_name("facebook/react")
    assert saved_project is not None
    assert len(saved_project.topics) == 3


def test_save_project_without_topics(project_service: ProjectService) -> None:
    """topicsなしプロジェクト保存のテスト

    topicsを指定しない場合、topicsが空であることを確認します。
    """
    # 実行
    project = project_service.save_project(
        full_name="facebook/react",
        url="https://github.com/facebook/react",
        stars=250000,
        language="JavaScript",
        description="A JavaScript library",
        last_commit_date=datetime(2025, 10, 1),
        topics=None,
    )

    # 検証: topicsが空
    assert len(project.topics) == 0


def test_save_project_update_topics(project_service: ProjectService) -> None:
    """topics更新のテスト

    update_if_exists=True でtopicsを更新した場合、
    topicsが正しく更新されることを確認します。
    """
    # 事前準備: 最初のtopicsで保存
    first_project = project_service.save_project(
        full_name="facebook/react",
        url="https://github.com/facebook/react",
        stars=250000,
        language="JavaScript",
        description="A JavaScript library",
        last_commit_date=datetime(2025, 10, 1),
        topics=["react", "javascript"],
    )
    assert len(first_project.topics) == 2

    # 実行: topicsを更新
    updated_project = project_service.save_project(
        full_name="facebook/react",
        url="https://github.com/facebook/react",
        stars=250000,
        language="JavaScript",
        description="A JavaScript library",
        last_commit_date=datetime(2025, 10, 1),
        topics=["react", "frontend", "ui"],  # 変更
        update_if_exists=True,
    )

    # 検証: topicsが更新されている
    assert len(updated_project.topics) == 3
    topic_names = {topic.name for topic in updated_project.topics}
    assert topic_names == {"react", "frontend", "ui"}


def test_get_project_by_full_name_exists(project_service: ProjectService) -> None:
    """full_nameでプロジェクト取得（存在する場合）のテスト

    存在するfull_nameを指定した場合、正しいプロジェクトが返されることを確認します。
    """
    # 事前準備
    project_service.save_project(
        full_name="facebook/react",
        url="https://github.com/facebook/react",
        stars=250000,
        language="JavaScript",
        description="A JavaScript library",
        last_commit_date=datetime(2025, 10, 1),
    )

    # 実行
    project = project_service.get_project_by_full_name("facebook/react")

    # 検証
    assert project is not None
    assert project.full_name == "facebook/react"
    assert project.stars == 250000


def test_get_project_by_full_name_not_exists(project_service: ProjectService) -> None:
    """full_nameでプロジェクト取得（存在しない場合）のテスト

    存在しないfull_nameを指定した場合、Noneが返されることを確認します。
    """
    # 実行
    project = project_service.get_project_by_full_name("nonexistent/project")

    # 検証
    assert project is None


def test_get_all_projects(project_service: ProjectService) -> None:
    """全件取得のテスト

    複数のプロジェクトを作成後、全件取得できることを確認します。
    """
    # 事前準備
    project_service.save_project(
        full_name="facebook/react",
        url="https://github.com/facebook/react",
        stars=250000,
        language="JavaScript",
        description="React",
        last_commit_date=datetime(2025, 10, 1),
    )
    project_service.save_project(
        full_name="vuejs/vue",
        url="https://github.com/vuejs/vue",
        stars=210000,
        language="JavaScript",
        description="Vue",
        last_commit_date=datetime(2025, 9, 15),
    )

    # 実行
    all_projects = project_service.get_all_projects()

    # 検証
    assert len(all_projects) == 2
    full_names = {project.full_name for project in all_projects}
    assert full_names == {"facebook/react", "vuejs/vue"}


def test_get_all_projects_empty(project_service: ProjectService) -> None:
    """全件取得（空）のテスト

    プロジェクトが存在しない場合、空リストが返されることを確認します。
    """
    # 実行
    all_projects = project_service.get_all_projects()

    # 検証
    assert len(all_projects) == 0


def test_count_projects(project_service: ProjectService) -> None:
    """件数カウントのテスト

    プロジェクトの件数が正しくカウントされることを確認します。
    """
    # 事前準備
    project_service.save_project(
        full_name="facebook/react",
        url="https://github.com/facebook/react",
        stars=250000,
        language="JavaScript",
        description="React",
        last_commit_date=datetime(2025, 10, 1),
    )
    project_service.save_project(
        full_name="vuejs/vue",
        url="https://github.com/vuejs/vue",
        stars=210000,
        language="JavaScript",
        description="Vue",
        last_commit_date=datetime(2025, 9, 15),
    )

    # 実行
    count = project_service.count_projects()

    # 検証
    assert count == 2


def test_count_projects_empty(project_service: ProjectService) -> None:
    """件数カウント（空）のテスト

    プロジェクトが存在しない場合、0が返されることを確認します。
    """
    # 実行
    count = project_service.count_projects()

    # 検証
    assert count == 0


def test_update_js_lines_count_success(project_service: ProjectService) -> None:
    """JS行数の更新（正常系）のテスト

    プロジェクトのJS行数を正常に更新できることを確認します。
    """
    # 準備: プロジェクトを作成
    project = project_service.save_project(
        full_name="facebook/react",
        url="https://github.com/facebook/react",
        stars=250000,
        language="JavaScript",
        description="A JavaScript library",
        last_commit_date=datetime(2025, 10, 1),
    )
    assert project.js_lines_count is None

    # 実行: JS行数を更新
    project_service.update_js_lines_count(project.id, 50000)

    # 検証: 更新されたことを確認
    updated_project = project_service.get_project_by_full_name("facebook/react")
    assert updated_project is not None
    assert updated_project.js_lines_count == 50000


def test_update_js_lines_count_zero(project_service: ProjectService) -> None:
    """JS行数の更新（0行）のテスト

    JSファイルが存在しないプロジェクトで0行を設定できることを確認します。
    """
    # 準備: プロジェクトを作成
    project = project_service.save_project(
        full_name="python/cpython",
        url="https://github.com/python/cpython",
        stars=100000,
        language="Python",
        description="Python language",
        last_commit_date=datetime(2025, 10, 1),
    )

    # 実行: 0行を設定
    project_service.update_js_lines_count(project.id, 0)

    # 検証
    updated_project = project_service.get_project_by_full_name("python/cpython")
    assert updated_project is not None
    assert updated_project.js_lines_count == 0


def test_update_js_lines_count_nonexistent_project(
    project_service: ProjectService,
) -> None:
    """JS行数の更新（存在しないプロジェクト）のテスト

    存在しないプロジェクトIDを指定した場合、ValueErrorが発生することを確認します。
    """
    # 実行と検証
    with pytest.raises(ValueError, match="Project with id 99999 not found"):
        project_service.update_js_lines_count(99999, 1000)


def test_update_js_lines_count_negative_value(project_service: ProjectService) -> None:
    """JS行数の更新（負の値）のテスト

    負の値を指定した場合、ValueErrorが発生することを確認します。
    """
    # 準備: プロジェクトを作成
    project = project_service.save_project(
        full_name="facebook/react",
        url="https://github.com/facebook/react",
        stars=250000,
        language="JavaScript",
        description="A JavaScript library",
        last_commit_date=datetime(2025, 10, 1),
    )

    # 実行と検証
    with pytest.raises(ValueError, match="js_lines_count must be non-negative"):
        project_service.update_js_lines_count(project.id, -100)
