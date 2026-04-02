# Setup VENV via UV

VENV_DIR=".venv"

# Check if UV is installed
if ! command -v uv &> /dev/null
then
    echo "UV is not installed. Please install UV to manage your virtual environments."
    exit 1
fi

# Create a virtual environment using UV
uv venv create $VENV_DIR

# Activate the virtual environment
source $VENV_DIR/bin/activate

echo "Virtual environment created and activated at $VENV_DIR"

# Install dependencies from uv.lock if it exists
if [ -f "uv.lock" ]; then
    echo "Installing dependencies from uv.lock..."
    # include dev and test dependencies
    uv sync --all-extras
else
    echo "No uv.lock file found. You can add dependencies to your project and run 'uv sync' to install them."
fi

# Install prek hooks if prek.yml exists
if [ -f "prek.toml" ]; then
    echo "Installing prek hooks..."
    prek install
else
    echo "No prek.yml file found. You can create one to define your pre-commit hooks."
fi
