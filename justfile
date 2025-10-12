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

# -----------------------------------------------------------------------------
# コードの品質管理 (Code Quality) ✨
# -----------------------------------------------------------------------------

# プロジェクトをフォーマットする
format:
    @echo "🎨 Formatting code with Ruff..."
    uvx ruff format .

# プロジェクトの静的解析(Lint)を実行する
lint:
    @echo "🔬 Linting code with Ruff..."
    uvx ruff check .

# フォーマットと自動修正をまとめて実行する
fix: format
    uvx ruff check . --fix

# 型チェックを実行する
typecheck:
    @echo "🔍 Running type check with Pyright..."
    uv run pyright
