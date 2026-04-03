# Setup VENV via UV

VENV_DIR=".venv"

# Check if UV is installed
if ! command -v uv &> /dev/null
then
    echo "❌ UV is not installed. Please install UV to manage your virtual environments."
    exit 1
fi

# Create a virtual environment using UV
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists at $VENV_DIR. Skipping creation."
else
    echo "⏳ Creating virtual environment at $VENV_DIR..."
    uv venv $VENV_DIR
    echo "✅ Virtual environment created successfully."
fi

# Activate the virtual environment
source $VENV_DIR/bin/activate

echo "✅ Virtual environment created and activated at $VENV_DIR"

# Install dependencies from uv.lock if it exists
if [ -f "uv.lock" ]; then
    echo "⏳ Installing dependencies from uv.lock..."
else
    echo "❌ No uv.lock file found. Running uv lock for you..."
    uv lock
    echo "✅ uv.lock created successfully."
fi

uv sync --all-extras
echo "✅ Dependencies installed successfully."

if [ -f "prek.toml" ]; then
    echo "⏳ Installing prek hooks..."
    uv run prek install
    echo "✅ prek hooks installed successfully."
else
    echo "No prek.yml file found. You can create one to define your pre-commit hooks."
fi

echo "✅ Setup complete!"
