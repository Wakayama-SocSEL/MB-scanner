"""JSLineCounterのテスト"""

from pathlib import Path

import pytest

from mb_scanner.lib.code_counter.js_counter import JSLinesCounter


class TestJSLinesCounter:
    """JSLinesCounterクラスのテスト"""

    def test_count_lines_in_single_js_file(self, tmp_path: Path) -> None:
        """単一のJSファイルの行数をカウントできる"""
        # Arrange
        js_file = tmp_path / "test.js"
        js_file.write_text("console.log('hello');\nconsole.log('world');\n")
        counter = JSLinesCounter()

        # Act
        result = counter.count_lines_in_file(js_file)

        # Assert
        assert result == 2

    def test_count_lines_in_empty_file(self, tmp_path: Path) -> None:
        """空のJSファイルは0行とカウントされる"""
        # Arrange
        js_file = tmp_path / "empty.js"
        js_file.write_text("")
        counter = JSLinesCounter()

        # Act
        result = counter.count_lines_in_file(js_file)

        # Assert
        assert result == 0

    def test_count_lines_with_empty_lines_and_comments(self, tmp_path: Path) -> None:
        """空行とコメント行を含む行数をカウントできる"""
        # Arrange
        js_file = tmp_path / "test.js"
        content = """// This is a comment
console.log('hello');

/* Multi-line
   comment */
console.log('world');
"""
        js_file.write_text(content)
        counter = JSLinesCounter()

        # Act
        result = counter.count_lines_in_file(js_file)

        # Assert
        assert result == 6  # 全行数（空行・コメント含む）

    def test_count_lines_with_different_extensions(self, tmp_path: Path) -> None:
        """異なる拡張子（.jsx, .mjs, .cjs）のファイルをカウントできる"""
        # Arrange
        extensions = ["jsx", "mjs", "cjs"]
        counter = JSLinesCounter()

        for ext in extensions:
            js_file = tmp_path / f"test.{ext}"
            js_file.write_text("console.log('test');\n")

            # Act
            result = counter.count_lines_in_file(js_file)

            # Assert
            assert result == 1, f"Failed for .{ext} extension"

    def test_count_lines_in_nonexistent_file(self, tmp_path: Path) -> None:
        """存在しないファイルは0行を返す"""
        # Arrange
        nonexistent = tmp_path / "nonexistent.js"
        counter = JSLinesCounter()

        # Act
        result = counter.count_lines_in_file(nonexistent)

        # Assert
        assert result == 0

    def test_count_lines_in_directory_with_multiple_files(self, tmp_path: Path) -> None:
        """ディレクトリ内の複数のJSファイルの総行数をカウントできる"""
        # Arrange
        (tmp_path / "file1.js").write_text("line1\nline2\n")
        (tmp_path / "file2.js").write_text("line3\nline4\nline5\n")
        (tmp_path / "file3.jsx").write_text("line6\n")
        counter = JSLinesCounter()

        # Act
        result = counter.count_lines_in_directory(tmp_path)

        # Assert
        assert result == 6  # 2 + 3 + 1

    def test_count_lines_in_empty_directory(self, tmp_path: Path) -> None:
        """空のディレクトリは0行を返す"""
        # Arrange
        counter = JSLinesCounter()

        # Act
        result = counter.count_lines_in_directory(tmp_path)

        # Assert
        assert result == 0

    def test_count_lines_in_directory_without_js_files(self, tmp_path: Path) -> None:
        """JSファイルが存在しないディレクトリは0行を返す"""
        # Arrange
        (tmp_path / "test.py").write_text("print('hello')\n")
        (tmp_path / "test.txt").write_text("hello world\n")
        counter = JSLinesCounter()

        # Act
        result = counter.count_lines_in_directory(tmp_path)

        # Assert
        assert result == 0

    def test_count_lines_in_nested_directory(self, tmp_path: Path) -> None:
        """ネストされたディレクトリ構造でもカウントできる"""
        # Arrange
        (tmp_path / "file1.js").write_text("line1\n")
        subdir = tmp_path / "src"
        subdir.mkdir()
        (subdir / "file2.js").write_text("line2\nline3\n")
        nested_subdir = subdir / "components"
        nested_subdir.mkdir()
        (nested_subdir / "file3.jsx").write_text("line4\nline5\nline6\n")
        counter = JSLinesCounter()

        # Act
        result = counter.count_lines_in_directory(tmp_path)

        # Assert
        assert result == 6  # 1 + 2 + 3

    def test_count_lines_ignores_non_js_files_in_mixed_directory(self, tmp_path: Path) -> None:
        """JSファイル以外は無視される"""
        # Arrange
        (tmp_path / "file1.js").write_text("line1\nline2\n")
        (tmp_path / "file2.py").write_text("line3\nline4\nline5\n")
        (tmp_path / "file3.txt").write_text("line6\n")
        (tmp_path / "README.md").write_text("# Title\n")
        counter = JSLinesCounter()

        # Act
        result = counter.count_lines_in_directory(tmp_path)

        # Assert
        assert result == 2  # .jsファイルのみ

    def test_count_lines_with_binary_file(self, tmp_path: Path) -> None:
        """バイナリファイルはスキップされる"""
        # Arrange
        js_file = tmp_path / "valid.js"
        js_file.write_text("console.log('hello');\n")

        binary_file = tmp_path / "binary.js"
        binary_file.write_bytes(b"\x00\x01\x02\x03\xff\xfe")

        counter = JSLinesCounter()

        # Act
        result = counter.count_lines_in_directory(tmp_path)

        # Assert
        # バイナリファイルはスキップされ、有効なJSファイルのみカウント
        assert result == 1

    def test_count_lines_in_directory_with_symlinks(self, tmp_path: Path) -> None:
        """シンボリックリンクは適切に処理される"""
        # Arrange
        real_file = tmp_path / "real.js"
        real_file.write_text("line1\nline2\n")

        # シンボリックリンクの作成
        link_file = tmp_path / "link.js"
        try:
            link_file.symlink_to(real_file)
        except OSError:
            # シンボリックリンク作成に失敗した場合（Windows等）はスキップ
            pytest.skip("Symbolic links not supported on this platform")

        counter = JSLinesCounter()

        # Act
        result = counter.count_lines_in_directory(tmp_path)

        # Assert
        # シンボリックリンクも通常のファイルとしてカウント
        assert result >= 2

    def test_count_lines_in_nonexistent_directory(self, tmp_path: Path) -> None:
        """存在しないディレクトリは0行を返す"""
        # Arrange
        nonexistent_dir = tmp_path / "nonexistent"
        counter = JSLinesCounter()

        # Act
        result = counter.count_lines_in_directory(nonexistent_dir)

        # Assert
        assert result == 0
