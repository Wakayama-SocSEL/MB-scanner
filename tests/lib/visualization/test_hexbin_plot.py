"""hexbinプロット生成ライブラリのテストモジュール"""

from pathlib import Path

import matplotlib.pyplot as plt
import pytest

from mb_scanner.lib.visualization.scatter_plot import create_hexbin_plot


class TestCreateHexbinPlot:
    """create_hexbin_plot関数のテスト"""

    def test_create_hexbin_plot_basic(self, tmp_path: Path) -> None:
        """基本的なhexbinプロット生成テスト"""
        data = [
            (1000, 10, "test/repo1"),
            (2000, 25, "test/repo2"),
            (1500, 5, "test/repo3"),
            (3000, 50, "test/repo4"),
            (2500, 30, "test/repo5"),
        ]
        output_path = tmp_path / "hexbin.png"

        create_hexbin_plot(data, output_path)

        # ファイルが作成されたことを確認
        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_hexbin_plot_with_gridsize(self, tmp_path: Path) -> None:
        """gridsizeのカスタマイズテスト"""
        data = [
            (1000, 10, "test/repo1"),
            (2000, 25, "test/repo2"),
            (1500, 5, "test/repo3"),
        ]
        output_path = tmp_path / "hexbin_gridsize.png"

        create_hexbin_plot(data, output_path, gridsize=30)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_hexbin_plot_with_cmap(self, tmp_path: Path) -> None:
        """カラーマップのカスタマイズテスト"""
        data = [
            (1000, 10, "test/repo1"),
            (2000, 25, "test/repo2"),
            (1500, 5, "test/repo3"),
        ]
        output_path = tmp_path / "hexbin_cmap.png"

        create_hexbin_plot(data, output_path, cmap="viridis")

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_hexbin_plot_with_log_scale_x(self, tmp_path: Path) -> None:
        """X軸対数軸でのhexbinプロット生成テスト"""
        data = [
            (100, 10, "test/repo1"),
            (1000, 25, "test/repo2"),
            (10000, 5, "test/repo3"),
        ]
        output_path = tmp_path / "hexbin_log_x.png"

        create_hexbin_plot(data, output_path, log_scale_x=True)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_hexbin_plot_with_log_scale_y(self, tmp_path: Path) -> None:
        """Y軸対数軸でのhexbinプロット生成テスト"""
        data = [
            (1000, 1, "test/repo1"),
            (2000, 10, "test/repo2"),
            (1500, 100, "test/repo3"),
        ]
        output_path = tmp_path / "hexbin_log_y.png"

        create_hexbin_plot(data, output_path, log_scale_y=True)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_hexbin_plot_with_log_scale_both(self, tmp_path: Path) -> None:
        """両軸対数軸でのhexbinプロット生成テスト"""
        data = [
            (100, 1, "test/repo1"),
            (1000, 10, "test/repo2"),
            (10000, 100, "test/repo3"),
        ]
        output_path = tmp_path / "hexbin_log_both.png"

        create_hexbin_plot(data, output_path, log_scale_x=True, log_scale_y=True)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_hexbin_plot_empty_data(self, tmp_path: Path) -> None:
        """空データのエラーハンドリングテスト"""
        data: list[tuple[int, int, str]] = []
        output_path = tmp_path / "hexbin_empty.png"

        with pytest.raises(ValueError, match="データが空です"):
            create_hexbin_plot(data, output_path)

        plt.close("all")

    def test_create_hexbin_plot_single_point(self, tmp_path: Path) -> None:
        """単一データポイントの処理テスト"""
        data = [(1000, 10, "test/repo1")]
        output_path = tmp_path / "hexbin_single.png"

        create_hexbin_plot(data, output_path)

        # 単一ポイントでもファイルが作成されることを確認
        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_hexbin_plot_with_custom_labels(self, tmp_path: Path) -> None:
        """カスタムラベルでのhexbinプロット生成テスト"""
        data = [
            (1000, 10, "test/repo1"),
            (2000, 25, "test/repo2"),
            (1500, 5, "test/repo3"),
        ]
        output_path = tmp_path / "hexbin_custom_labels.png"

        create_hexbin_plot(
            data,
            output_path,
            title="Custom Title",
            xlabel="Custom X Label",
            ylabel="Custom Y Label",
        )

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_hexbin_plot_creates_output_directory(self, tmp_path: Path) -> None:
        """出力ディレクトリが自動作成されるテスト"""
        data = [
            (1000, 10, "test/repo1"),
            (2000, 25, "test/repo2"),
        ]
        output_path = tmp_path / "subdir" / "nested" / "hexbin.png"

        create_hexbin_plot(data, output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_hexbin_plot_with_correlation(self, tmp_path: Path) -> None:
        """相関係数表示のテスト"""
        data = [
            (1000, 10, "test/repo1"),
            (2000, 25, "test/repo2"),
            (1500, 5, "test/repo3"),
            (3000, 35, "test/repo4"),
        ]
        output_path = tmp_path / "hexbin_correlation.png"

        create_hexbin_plot(data, output_path, show_correlation=True)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_hexbin_plot_with_regression(self, tmp_path: Path) -> None:
        """回帰直線表示のテスト"""
        data = [
            (1000, 10, "test/repo1"),
            (2000, 25, "test/repo2"),
            (1500, 5, "test/repo3"),
            (3000, 35, "test/repo4"),
        ]
        output_path = tmp_path / "hexbin_regression.png"

        create_hexbin_plot(data, output_path, show_regression=True)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_hexbin_plot_with_correlation_and_regression(self, tmp_path: Path) -> None:
        """相関係数と回帰直線の両方を表示するテスト"""
        data = [
            (1000, 10, "test/repo1"),
            (2000, 25, "test/repo2"),
            (1500, 5, "test/repo3"),
            (3000, 35, "test/repo4"),
        ]
        output_path = tmp_path / "hexbin_corr_and_regression.png"

        create_hexbin_plot(data, output_path, show_correlation=True, show_regression=True)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_hexbin_plot_regression_with_log_scale(self, tmp_path: Path) -> None:
        """対数軸での回帰直線表示テスト"""
        data = [
            (100, 1, "test/repo1"),
            (1000, 10, "test/repo2"),
            (10000, 100, "test/repo3"),
        ]
        output_path = tmp_path / "hexbin_regression_log.png"

        create_hexbin_plot(data, output_path, log_scale_x=True, log_scale_y=True, show_regression=True)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_hexbin_plot_correlation_with_single_point(self, tmp_path: Path) -> None:
        """単一ポイントでの相関係数（計算されない）のテスト"""
        data = [(1000, 10, "test/repo1")]
        output_path = tmp_path / "hexbin_corr_single.png"

        # 単一ポイントでは相関係数は計算されないが、エラーにはならない
        create_hexbin_plot(data, output_path, show_correlation=True)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_hexbin_plot_regression_with_single_point(self, tmp_path: Path) -> None:
        """単一ポイントでの回帰直線（計算されない）のテスト"""
        data = [(1000, 10, "test/repo1")]
        output_path = tmp_path / "hexbin_regression_single.png"

        # 単一ポイントでは回帰直線は計算されないが、エラーにはならない
        create_hexbin_plot(data, output_path, show_regression=True)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")
