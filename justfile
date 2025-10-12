# 利用可能なコマンドの一覧を表示する (デフォルトタスク)
default:
    @just --list

# -----------------------------------------------------------------------------
# 開発環境のセットアップ (Setup Development Environment) ⚙️
# -----------------------------------------------------------------------------

# Pythonの仮想環境を作成する
venv:
    @echo "🐍 Creating Python virtual environment..."
    uv venv

# Pythonの依存関係をインストールする (venvに依存)
python-deps: venv
    @echo "📦 Installing Python dependencies..."
    uv sync --dev
    uv pip install -e .
