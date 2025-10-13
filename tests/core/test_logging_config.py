"""logging_config のテスト"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from unittest.mock import patch

from mb_scanner.core.logging_config import get_logger, setup_logging


def test_setup_logging_default(tmp_path: Path):
    """デフォルト設定でログが正しく初期化されることを確認する"""
    # Arrange
    log_file = tmp_path / "test.log"

    # Act
    with patch("mb_scanner.core.logging_config.settings") as mock_settings:
        mock_settings.log_level = "INFO"
        mock_settings.effective_log_file = log_file
        mock_settings.log_to_console = True

        setup_logging()

    # Assert
    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO
    assert len(root_logger.handlers) >= 1  # 少なくとも1つのハンドラーが設定されている


def test_setup_logging_with_custom_level(tmp_path: Path):
    """カスタムログレベルで初期化されることを確認する"""
    # Arrange
    log_file = tmp_path / "test.log"

    # Act
    with patch("mb_scanner.core.logging_config.settings") as mock_settings:
        mock_settings.log_level = "INFO"
        mock_settings.effective_log_file = log_file
        mock_settings.log_to_console = False

        setup_logging(log_level="DEBUG")

    # Assert
    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG


def test_setup_logging_creates_log_file(tmp_path: Path):
    """ログファイルが作成されることを確認する"""
    # Arrange
    log_file = tmp_path / "logs" / "test.log"

    # Act
    with patch("mb_scanner.core.logging_config.settings") as mock_settings:
        mock_settings.log_level = "INFO"
        mock_settings.effective_log_file = log_file
        mock_settings.log_to_console = False

        setup_logging()

        # ログメッセージを出力
        test_logger = logging.getLogger("test")
        test_logger.info("Test message")

    # Assert
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "Test message" in content


def test_setup_logging_file_handler_only(tmp_path: Path):
    """コンソール出力なしでファイルのみに出力されることを確認する"""
    # Arrange
    log_file = tmp_path / "test.log"

    # Act
    with patch("mb_scanner.core.logging_config.settings") as mock_settings:
        mock_settings.log_level = "INFO"
        mock_settings.effective_log_file = log_file
        mock_settings.log_to_console = False

        setup_logging()

    # Assert
    root_logger = logging.getLogger()
    # ファイルハンドラーのみが存在する
    assert len(root_logger.handlers) == 1
    assert isinstance(root_logger.handlers[0], RotatingFileHandler)


def test_get_logger():
    """get_logger が正しくロガーを返すことを確認する"""
    # Act
    logger = get_logger("test_module")

    # Assert
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_module"


def test_setup_logging_clears_existing_handlers(tmp_path: Path):
    """既存のハンドラーがクリアされることを確認する"""
    # Arrange
    log_file = tmp_path / "test.log"
    root_logger = logging.getLogger()

    # 既存のハンドラーを追加
    existing_handler = logging.StreamHandler()
    root_logger.addHandler(existing_handler)

    # Act
    with patch("mb_scanner.core.logging_config.settings") as mock_settings:
        mock_settings.log_level = "INFO"
        mock_settings.effective_log_file = log_file
        mock_settings.log_to_console = False

        setup_logging()

    # Assert
    # ハンドラーがクリアされ、新しいハンドラーのみが設定されている
    assert len(root_logger.handlers) == 1
    assert root_logger.handlers[0] != existing_handler
