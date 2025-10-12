"""TopicService のテスト

このモジュールでは、TopicService の全機能をテストします。
"""

from mb_scanner.services.topic_service import TopicService


def test_get_or_create_topics_all_new(topic_service: TopicService) -> None:
    """全て新規作成のテスト

    存在しないtopicを複数指定した場合、全て新規作成されることを確認します。
    """
    topic_names = ["react", "javascript", "frontend"]

    # 実行
    topics = topic_service.get_or_create_topics(topic_names)

    # 検証
    assert len(topics) == 3
    assert topics[0].name == "react"
    assert topics[1].name == "javascript"
    assert topics[2].name == "frontend"

    # DBに保存されていることを確認
    all_topics = topic_service.get_all_topics()
    assert len(all_topics) == 3


def test_get_or_create_topics_all_existing(topic_service: TopicService) -> None:
    """全て既存のテスト

    既に存在するtopicを指定した場合、既存のものが返されることを確認します。
    """
    # 事前準備: topicを作成
    topic_names = ["react", "vue"]
    first_topics = topic_service.get_or_create_topics(topic_names)
    first_react_id = first_topics[0].id

    # 実行: 同じtopicを再度取得
    second_topics = topic_service.get_or_create_topics(topic_names)

    # 検証: 同じIDが返される（新規作成されていない）
    assert len(second_topics) == 2
    assert second_topics[0].id == first_react_id
    assert second_topics[0].name == "react"

    # DBには2件のみ存在
    all_topics = topic_service.get_all_topics()
    assert len(all_topics) == 2


def test_get_or_create_topics_mixed(topic_service: TopicService) -> None:
    """新規と既存が混在するテスト

    既存topicと新規topicが混在する場合、正しく処理されることを確認します。
    """
    # 事前準備: 一部のtopicを作成
    topic_service.get_or_create_topics(["react"])

    # 実行: 既存(react)と新規(vue, angular)が混在
    topics = topic_service.get_or_create_topics(["react", "vue", "angular"])

    # 検証
    assert len(topics) == 3
    assert topics[0].name == "react"
    assert topics[1].name == "vue"
    assert topics[2].name == "angular"

    # DBには3件存在
    all_topics = topic_service.get_all_topics()
    assert len(all_topics) == 3


def test_get_or_create_topics_empty(topic_service: TopicService) -> None:
    """空リストのテスト

    空リストを指定した場合、空リストが返されることを確認します。
    """
    # 実行
    topics = topic_service.get_or_create_topics([])

    # 検証
    assert len(topics) == 0

    # DBにも何も保存されていない
    all_topics = topic_service.get_all_topics()
    assert len(all_topics) == 0


def test_get_topic_by_name_exists(topic_service: TopicService) -> None:
    """名前でtopicを取得（存在する場合）のテスト

    存在するtopic名を指定した場合、正しいtopicが返されることを確認します。
    """
    # 事前準備
    topic_service.get_or_create_topics(["react", "vue"])

    # 実行
    topic = topic_service.get_topic_by_name("react")

    # 検証
    assert topic is not None
    assert topic.name == "react"


def test_get_topic_by_name_not_exists(topic_service: TopicService) -> None:
    """名前でtopicを取得（存在しない場合）のテスト

    存在しないtopic名を指定した場合、Noneが返されることを確認します。
    """
    # 実行
    topic = topic_service.get_topic_by_name("nonexistent")

    # 検証
    assert topic is None


def test_get_all_topics(topic_service: TopicService) -> None:
    """全件取得のテスト

    複数のtopicを作成後、全件取得できることを確認します。
    """
    # 事前準備
    topic_service.get_or_create_topics(["react", "vue", "angular"])

    # 実行
    all_topics = topic_service.get_all_topics()

    # 検証
    assert len(all_topics) == 3
    topic_names = {topic.name for topic in all_topics}
    assert topic_names == {"react", "vue", "angular"}


def test_get_all_topics_empty(topic_service: TopicService) -> None:
    """全件取得（空）のテスト

    topicが存在しない場合、空リストが返されることを確認します。
    """
    # 実行
    all_topics = topic_service.get_all_topics()

    # 検証
    assert len(all_topics) == 0


def test_count_topics(topic_service: TopicService) -> None:
    """件数カウントのテスト

    topicの件数が正しくカウントされることを確認します。
    """
    # 事前準備
    topic_service.get_or_create_topics(["react", "vue"])

    # 実行
    count = topic_service.count_topics()

    # 検証
    assert count == 2


def test_count_topics_empty(topic_service: TopicService) -> None:
    """件数カウント（空）のテスト

    topicが存在しない場合、0が返されることを確認します。
    """
    # 実行
    count = topic_service.count_topics()

    # 検証
    assert count == 0
