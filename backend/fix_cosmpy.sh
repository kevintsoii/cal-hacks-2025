#!/bin/bash
# Fix cosmpy protobuf shadowing issue
# Run this script after installing dependencies if you encounter protobuf import errors
# Works with both venv (local development) and system-wide installs (Docker)

set -e

# Detect Python site-packages location
if [ -n "$VIRTUAL_ENV" ]; then
    # Running in a virtual environment
    PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    SITE_PACKAGES="$VIRTUAL_ENV/lib/python${PYTHON_VERSION}/site-packages"
    echo "Detected venv installation at: $SITE_PACKAGES"
elif [ -d "$(pwd)/.venv" ]; then
    # venv exists but not activated
    PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    SITE_PACKAGES="$(pwd)/.venv/lib/python${PYTHON_VERSION}/site-packages"
    echo "Detected venv installation at: $SITE_PACKAGES"
else
    # System-wide installation (Docker)
    SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")
    echo "Detected system-wide installation at: $SITE_PACKAGES"
fi

COSMPY_GOOGLE_PATH="$SITE_PACKAGES/cosmpy/protos/google"

if [ ! -d "$COSMPY_GOOGLE_PATH" ]; then
    echo "✓ cosmpy not installed or already fixed."
    exit 0
fi

if [ -f "$COSMPY_GOOGLE_PATH/__init__.py" ]; then
    echo "Fixing cosmpy protobuf shadowing..."
    mv "$COSMPY_GOOGLE_PATH/__init__.py" "$COSMPY_GOOGLE_PATH/__init__.py.bak"
    mv "$COSMPY_GOOGLE_PATH/protobuf/__init__.py" "$COSMPY_GOOGLE_PATH/protobuf/__init__.py.bak" 2>/dev/null || true
    echo "✓ Fixed! cosmpy will no longer shadow the protobuf package."
else
    echo "✓ Already fixed."
fi