"""config のテスト"""

from pathlib import Path

from mb_scanner.core.config import Settings


def test_effective_codeql_output_dir_default(tmp_path: Path):
    """デフォルトで outputs/queries が返されることを確認する"""
    # Arrange
    settings = Settings(codeql_output_base_dir=tmp_path / "outputs" / "queries")

    # Act
    output_dir = settings.effective_codeql_output_dir

    # Assert
    assert output_dir == tmp_path / "outputs" / "queries"
    assert output_dir.exists()  # ディレクトリが作成されることを確認


def test_effective_codeql_output_dir_custom(tmp_path: Path):
    """カスタム設定が正しく反映されることを確認する"""
    # Arrange
    custom_dir = tmp_path / "custom" / "output"
    settings = Settings(codeql_output_base_dir=custom_dir)

    # Act
    output_dir = settings.effective_codeql_output_dir

    # Assert
    assert output_dir == custom_dir
    assert output_dir.exists()  # ディレクトリが作成されることを確認


def test_get_codeql_output_path_basic(tmp_path: Path):
    """プロジェクト名とクエリファイルから正しいパスが生成されることを確認する"""
    # Arrange
    settings = Settings(codeql_output_base_dir=tmp_path / "outputs" / "queries")
    query_file = Path("codeql/queries/id_10.ql")

    # Act
    output_path = settings.get_codeql_output_path("facebook/react", query_file)

    # Assert
    assert output_path == tmp_path / "outputs" / "queries" / "id_10" / "facebook-react.sarif"


def test_get_codeql_output_path_with_slash(tmp_path: Path):
    """プロジェクト名のスラッシュがハイフンに変換されることを確認する"""
    # Arrange
    settings = Settings(codeql_output_base_dir=tmp_path / "outputs" / "queries")
    query_file = Path("codeql/queries/id_20.ql")

    # Act
    output_path = settings.get_codeql_output_path("microsoft/vscode", query_file)

    # Assert
    assert output_path == tmp_path / "outputs" / "queries" / "id_20" / "microsoft-vscode.sarif"


def test_get_codeql_output_path_custom_base_dir(tmp_path: Path):
    """カスタムベースディレクトリでも正しいパスが生成されることを確認する"""
    # Arrange
    custom_dir = tmp_path / "custom" / "output"
    settings = Settings(codeql_output_base_dir=custom_dir)
    query_file = Path("queries/my_query.ql")

    # Act
    output_path = settings.get_codeql_output_path("facebook/react", query_file)

    # Assert
    assert output_path == custom_dir / "my_query" / "facebook-react.sarif"


def test_codeql_default_output_format():
    """デフォルトの出力フォーマットが正しく設定されることを確認する"""
    # Arrange & Act
    settings = Settings()

    # Assert
    assert settings.codeql_default_output_format == "sarifv2.1.0"


def test_effective_codeql_clone_dir_default(tmp_path: Path):
    """デフォルトで data/repositories が返されることを確認する"""
    # Arrange
    data_dir = tmp_path / "data"
    settings = Settings(data_dir=data_dir)

    # Act
    clone_dir = settings.effective_codeql_clone_dir

    # Assert
    assert clone_dir == data_dir / "repositories"
    assert clone_dir.exists()  # ディレクトリが作成されることを確認


def test_effective_codeql_clone_dir_custom(tmp_path: Path):
    """カスタム設定が正しく反映されることを確認する"""
    # Arrange
    custom_dir = tmp_path / "custom" / "clones"
    settings = Settings(codeql_clone_base_dir=custom_dir)

    # Act
    clone_dir = settings.effective_codeql_clone_dir

    # Assert
    assert clone_dir == custom_dir
    assert clone_dir.exists()  # ディレクトリが作成されることを確認
