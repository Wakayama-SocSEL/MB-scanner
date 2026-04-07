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

typecheck-ts:
    @echo "🔍 Running TypeScript type check with pnpm script..."
    pnpm --prefix mb_scanner/resources/benchmark run typecheck

# -----------------------------------------------------------------------------
# TypeScript Build (TypeScript ビルド) 🧱
# -----------------------------------------------------------------------------

# benchmark の TypeScript を単発ビルドする
build-benchmark-ts:
    @echo "🧱 Building TypeScript with pnpm script..."
    pnpm --prefix mb_scanner/resources/benchmark run build

# benchmark の TypeScript を watch モードでビルドする
watch-benchmark-ts:
    @echo "👀 Watching TypeScript build with pnpm script..."
    pnpm --prefix mb_scanner/resources/benchmark run build:watch

# benchmark の TypeScript watch を停止する
stop-benchmark-watch:
    @echo "🛑 Stopping TypeScript watch processes..."
    pkill -f 'node build.mjs --watch' || true
    pkill -f 'pnpm --prefix mb_scanner/resources/benchmark run build:watch' || true
    pkill -f 'esbuild .*runner.ts.*--watch' || true

# -----------------------------------------------------------------------------
# データベース管理 (Database Management) 🗄️
# -----------------------------------------------------------------------------

# データベースマイグレーションを実行する
migrate:
    @echo "🔄 Running database migrations..."
    uv run mb-scanner migrate

# データベースマイグレーションのドライラン（確認のみ）
migrate-dry-run:
    @echo "🔍 Checking pending migrations (dry run)..."
    uv run mb-scanner migrate --dry-run

# -----------------------------------------------------------------------------
# ファイル同期 (File Synchronization) 🔄
# -----------------------------------------------------------------------------

# brain-1サーバへファイルを同期する
sync-to-brain1:
    @echo "📤 Syncing files to brain-1..."
    rsync -av --exclude-from=exclude-list.txt . brain-1:/mnt/data1/tomoya-n/MB-Scanner
    @echo "✅ Sync completed!"

# brain-2サーバへファイルを同期する
sync-to-brain2:
    @echo "📤 Syncing files to brain-2..."
    rsync -av --exclude-from=exclude-list.txt . brain-2:/mnt/data1/tomoya-n/MB-Scanner
    @echo "✅ Sync completed!"
