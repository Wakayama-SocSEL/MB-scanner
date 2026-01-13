"""散布図生成ライブラリのテストモジュール"""

from pathlib import Path

import matplotlib.pyplot as plt

from mb_scanner.lib.visualization.scatter_plot import create_scatter_plot


class TestCreateScatterPlot:
    """create_scatter_plot関数のテスト"""

    def test_create_scatter_plot_success(self, tmp_path: Path) -> None:
        """正常な散布図生成テスト"""
        data = [
            (1000, 10, "test/repo1"),
            (2000, 25, "test/repo2"),
            (1500, 5, "test/repo3"),
            (3000, 50, "test/repo4"),
        ]
        output_path = tmp_path / "scatter.png"

        create_scatter_plot(data, output_path)

        # ファイルが作成されたことを確認
        assert output_path.exists()
        assert output_path.stat().st_size > 0

        # matplotlibのクリーンアップ
        plt.close("all")

    def test_create_scatter_plot_empty_data(self, tmp_path: Path) -> None:
        """空データの処理テスト"""
        data: list[tuple[int, int, str]] = []
        output_path = tmp_path / "scatter_empty.png"

        create_scatter_plot(data, output_path)

        # 空データでもファイルが作成されることを確認
        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_scatter_plot_single_point(self, tmp_path: Path) -> None:
        """単一データポイントの処理テスト"""
        data = [(1000, 10, "test/repo1")]
        output_path = tmp_path / "scatter_single.png"

        create_scatter_plot(data, output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_scatter_plot_custom_labels(self, tmp_path: Path) -> None:
        """カスタムラベルの適用テスト"""
        data = [
            (1000, 10, "test/repo1"),
            (2000, 25, "test/repo2"),
        ]
        output_path = tmp_path / "scatter_custom.png"
        custom_title = "Custom Title"
        custom_xlabel = "Custom X Label"
        custom_ylabel = "Custom Y Label"

        create_scatter_plot(data, output_path, title=custom_title, xlabel=custom_xlabel, ylabel=custom_ylabel)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_scatter_plot_output_directory_creation(self, tmp_path: Path) -> None:
        """出力ディレクトリの自動作成テスト"""
        nested_output_path = tmp_path / "nested" / "dir" / "scatter.png"

        data = [(1000, 10, "test/repo1")]

        create_scatter_plot(data, nested_output_path)

        # ディレクトリが自動作成され、ファイルが存在することを確認
        assert nested_output_path.exists()
        assert nested_output_path.stat().st_size > 0

        plt.close("all")

    def test_create_scatter_plot_with_log_scale_x(self, tmp_path: Path) -> None:
        """x軸を対数軸にした散布図生成テスト"""
        data = [
            (100, 10, "test/repo1"),
            (1000, 25, "test/repo2"),
            (10000, 50, "test/repo3"),
        ]
        output_path = tmp_path / "scatter_log_scale.png"

        create_scatter_plot(data, output_path, log_scale_x=True)

        # ファイルが作成されたことを確認
        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_scatter_plot_without_log_scale_x(self, tmp_path: Path) -> None:
        """x軸を線形軸（デフォルト）にした散布図生成テスト"""
        data = [
            (1000, 10, "test/repo1"),
            (2000, 25, "test/repo2"),
        ]
        output_path = tmp_path / "scatter_linear.png"

        # log_scale_xを明示的にFalseで指定
        create_scatter_plot(data, output_path, log_scale_x=False)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_scatter_plot_with_log_scale_y(self, tmp_path: Path) -> None:
        """y軸を対数軸にした散布図生成テスト"""
        data = [
            (1000, 10, "test/repo1"),
            (2000, 100, "test/repo2"),
            (3000, 1000, "test/repo3"),
        ]
        output_path = tmp_path / "scatter_log_scale_y.png"

        create_scatter_plot(data, output_path, log_scale_y=True)

        # ファイルが作成されたことを確認
        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_scatter_plot_without_log_scale_y(self, tmp_path: Path) -> None:
        """y軸を線形軸（デフォルト）にした散布図生成テスト"""
        data = [
            (1000, 10, "test/repo1"),
            (2000, 25, "test/repo2"),
        ]
        output_path = tmp_path / "scatter_linear_y.png"

        # log_scale_yを明示的にFalseで指定
        create_scatter_plot(data, output_path, log_scale_y=False)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_scatter_plot_with_both_log_scales(self, tmp_path: Path) -> None:
        """x軸とy軸の両方を対数軸にした散布図生成テスト"""
        data = [
            (100, 10, "test/repo1"),
            (1000, 100, "test/repo2"),
            (10000, 1000, "test/repo3"),
        ]
        output_path = tmp_path / "scatter_log_both.png"

        create_scatter_plot(data, output_path, log_scale_x=True, log_scale_y=True)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_scatter_plot_with_correlation(self, tmp_path: Path) -> None:
        """スピアマン相関係数を表示した散布図生成テスト"""
        data = [
            (1000, 10, "test/repo1"),
            (2000, 25, "test/repo2"),
            (1500, 15, "test/repo3"),
            (3000, 35, "test/repo4"),
        ]
        output_path = tmp_path / "scatter_correlation.png"

        create_scatter_plot(data, output_path, show_correlation=True)

        # ファイルが作成されたことを確認
        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_scatter_plot_without_correlation(self, tmp_path: Path) -> None:
        """スピアマン相関係数なしで散布図生成テスト"""
        data = [
            (1000, 10, "test/repo1"),
            (2000, 25, "test/repo2"),
        ]
        output_path = tmp_path / "scatter_no_correlation.png"

        create_scatter_plot(data, output_path, show_correlation=False)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_scatter_plot_correlation_with_single_point(self, tmp_path: Path) -> None:
        """1点のみのデータで相関係数表示を試みた場合のテスト"""
        data = [(1000, 10, "test/repo1")]
        output_path = tmp_path / "scatter_single_corr.png"

        # エラーにならず、グラフが生成されることを確認
        create_scatter_plot(data, output_path, show_correlation=True)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_scatter_plot_correlation_with_empty_data(self, tmp_path: Path) -> None:
        """空データで相関係数表示を試みた場合のテスト"""
        data: list[tuple[int, int, str]] = []
        output_path = tmp_path / "scatter_empty_corr.png"

        # エラーにならず、グラフが生成されることを確認
        create_scatter_plot(data, output_path, show_correlation=True)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_scatter_plot_with_regression(self, tmp_path: Path) -> None:
        """回帰直線を表示した散布図生成テスト"""
        data = [
            (1000, 10, "test/repo1"),
            (2000, 25, "test/repo2"),
            (1500, 15, "test/repo3"),
            (3000, 35, "test/repo4"),
        ]
        output_path = tmp_path / "scatter_regression.png"

        create_scatter_plot(data, output_path, show_regression=True)

        # ファイルが作成されたことを確認
        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_scatter_plot_without_regression(self, tmp_path: Path) -> None:
        """回帰直線なしで散布図生成テスト"""
        data = [
            (1000, 10, "test/repo1"),
            (2000, 25, "test/repo2"),
        ]
        output_path = tmp_path / "scatter_no_regression.png"

        create_scatter_plot(data, output_path, show_regression=False)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_scatter_plot_with_regression_log_scale_x(self, tmp_path: Path) -> None:
        """x軸対数スケール + 回帰直線の散布図生成テスト"""
        data = [
            (100, 10, "test/repo1"),
            (1000, 25, "test/repo2"),
            (10000, 50, "test/repo3"),
        ]
        output_path = tmp_path / "scatter_regression_log_x.png"

        create_scatter_plot(data, output_path, log_scale_x=True, show_regression=True)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_scatter_plot_with_regression_log_scale_y(self, tmp_path: Path) -> None:
        """y軸対数スケール + 回帰直線の散布図生成テスト"""
        data = [
            (1000, 10, "test/repo1"),
            (2000, 100, "test/repo2"),
            (3000, 1000, "test/repo3"),
        ]
        output_path = tmp_path / "scatter_regression_log_y.png"

        create_scatter_plot(data, output_path, log_scale_y=True, show_regression=True)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_scatter_plot_with_regression_both_log_scales(self, tmp_path: Path) -> None:
        """両軸対数スケール + 回帰直線の散布図生成テスト"""
        data = [
            (100, 10, "test/repo1"),
            (1000, 100, "test/repo2"),
            (10000, 1000, "test/repo3"),
        ]
        output_path = tmp_path / "scatter_regression_log_both.png"

        create_scatter_plot(data, output_path, log_scale_x=True, log_scale_y=True, show_regression=True)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_scatter_plot_regression_with_single_point(self, tmp_path: Path) -> None:
        """1点のみのデータで回帰直線表示を試みた場合のテスト"""
        data = [(1000, 10, "test/repo1")]
        output_path = tmp_path / "scatter_single_regression.png"

        # エラーにならず、グラフが生成されることを確認
        create_scatter_plot(data, output_path, show_regression=True)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_scatter_plot_regression_with_empty_data(self, tmp_path: Path) -> None:
        """空データで回帰直線表示を試みた場合のテスト"""
        data: list[tuple[int, int, str]] = []
        output_path = tmp_path / "scatter_empty_regression.png"

        # エラーにならず、グラフが生成されることを確認
        create_scatter_plot(data, output_path, show_regression=True)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_scatter_plot_with_correlation_and_regression(self, tmp_path: Path) -> None:
        """相関係数と回帰直線を同時表示するテスト"""
        data = [
            (1000, 10, "test/repo1"),
            (2000, 25, "test/repo2"),
            (1500, 15, "test/repo3"),
            (3000, 35, "test/repo4"),
        ]
        output_path = tmp_path / "scatter_corr_and_regression.png"

        create_scatter_plot(data, output_path, show_correlation=True, show_regression=True)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")
