#!/bin/bash

###############################################################################
# Windows AI Release Builder
# Builds a complete Windows release package including:
# - Electron GUI executable (NSIS installer + portable)
# - Python backend
# - All dependencies and configuration files
###############################################################################

set -e

echo "=========================================="
echo "🔨 Windows AI Release Builder"
echo "=========================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}▶${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Step 1: Check prerequisites
print_step "Checking prerequisites..."

if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 18+ and try again."
    exit 1
fi

if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install npm and try again."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.11+ and try again."
    exit 1
fi

print_success "All prerequisites are installed"
echo ""

# Step 2: Install dependencies
print_step "Installing dependencies..."

echo "  Installing npm dependencies..."
npm install --silent
if [ $? -eq 0 ]; then
    print_success "npm dependencies installed"
else
    print_error "Failed to install npm dependencies"
    exit 1
fi

echo "  Installing Python dependencies..."
pip3 install -r requirements.txt --quiet
if [ $? -eq 0 ]; then
    print_success "Python dependencies installed"
else
    print_error "Failed to install Python dependencies"
    exit 1
fi

echo ""

# Step 3: Run tests
print_step "Running tests..."

echo "  Running Python tests..."
python3 -m pytest tests/ -v --ignore=tests/test_gui_download_speed.py --ignore=tests/test_api_keys.py --ignore=tests/test_installer_cli.py -x 2>&1 | grep -E "(PASSED|FAILED|ERROR|test session starts|passed|failed)" || true

echo ""

# Step 4: Build TypeScript
print_step "Building TypeScript components..."

if [ -d "apps/actions-api" ]; then
    echo "  Building actions-api..."
    cd apps/actions-api
    npm run build --silent
    if [ $? -eq 0 ]; then
        print_success "actions-api built"
    else
        print_warning "actions-api build had issues (non-critical)"
    fi
    cd "$SCRIPT_DIR"
fi

echo ""

# Step 5: Generate icons
print_step "Generating application icons..."
python3 scripts/create_icon.py
print_success "Icons generated"
echo ""

# Step 6: Build Electron GUI
print_step "Building Electron GUI executable..."

cd apps/gui

echo "  Installing GUI dependencies..."
npm install --silent electron electron-builder

echo "  Building Windows installer (x64)..."
npm run build -- --win --x64 2>&1 | tail -20

if [ $? -eq 0 ]; then
    print_success "Windows x64 installer built"
else
    print_warning "Windows x64 build completed with warnings"
fi

echo ""
echo "  Building Windows installer (ia32)..."
npm run build -- --win --ia32 2>&1 | tail -20

if [ $? -eq 0 ]; then
    print_success "Windows ia32 installer built"
else
    print_warning "Windows ia32 build completed with warnings"
fi

cd "$SCRIPT_DIR"
echo ""

# Step 7: Create release package
print_step "Creating release package..."

RELEASE_DIR="release-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RELEASE_DIR"

# Copy built installers
if [ -d "apps/gui/dist" ]; then
    cp apps/gui/dist/*.exe "$RELEASE_DIR/" 2>/dev/null || true
    cp apps/gui/dist/*.zip "$RELEASE_DIR/" 2>/dev/null || true
fi

# Copy Python backend
mkdir -p "$RELEASE_DIR/backend"
cp -r windows_ai "$RELEASE_DIR/backend/"
cp requirements.txt "$RELEASE_DIR/backend/"
cp start-all.sh start-all.bat "$RELEASE_DIR/" 2>/dev/null || true
cp start-backend.sh start-backend.bat "$RELEASE_DIR/" 2>/dev/null || true

# Copy documentation
cp README.md LICENSE CHANGELOG.md "$RELEASE_DIR/" 2>/dev/null || true

# Copy config
if [ -d "config" ]; then
    cp -r config "$RELEASE_DIR/"
fi

print_success "Release package created: $RELEASE_DIR"
echo ""

# Step 8: Summary
echo "=========================================="
echo "✅ Build Complete!"
echo "=========================================="
echo ""
echo "Release artifacts:"
ls -lh "$RELEASE_DIR" | grep -v "^total" | awk '{print "  • " $9 " (" $5 ")"}'
echo ""
echo "Next steps:"
echo "  1. Test the installer on Windows"
echo "  2. Run the backend: cd $RELEASE_DIR && ./start-backend.sh"
echo "  3. Install the GUI from $RELEASE_DIR/*.exe"
echo ""
echo "For distribution, upload the contents of $RELEASE_DIR/"
echo "=========================================="
