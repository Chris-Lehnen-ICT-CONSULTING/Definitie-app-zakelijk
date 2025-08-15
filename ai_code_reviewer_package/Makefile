# AI Code Reviewer Package - Build Makefile
# Vereenvoudigt build en publicatie workflow

.PHONY: help clean install build test test-local upload upload-test version lint security check-all validate-all

PACKAGE_NAME = ai-code-reviewer
PYTHON = python3
PIP = pip3

# Default target
help:
	@echo "AI Code Reviewer v2.0.0 - Build Commands"
	@echo ""
	@echo "Available targets:"
	@echo "  clean        - Clean build artifacts"
	@echo "  install      - Install package dependencies"
	@echo "  build        - Build package (source + wheel)"  
	@echo "  test-local   - Test package locally"
	@echo "  test         - Run test suite"
	@echo "  lint         - Run code quality checks"
	@echo "  security     - Run security scan"
	@echo "  check-all    - Run all quality checks"
	@echo "  validate-all - Full package validation"
	@echo "  upload-test  - Upload to Test PyPI"
	@echo "  upload       - Upload to PyPI" 
	@echo "  version      - Show package version"

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*.orig" -delete
	find . -name "*.rej" -delete
	@echo "✅ Clean completed"

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	$(PIP) install --upgrade pip setuptools wheel build twine
	$(PIP) install -e .
	@echo "✅ Dependencies installed"

# Install development dependencies
install-dev:
	@echo "🔧 Installing development dependencies..."
	$(PIP) install -e .[dev]
	$(PIP) install ruff black mypy bandit pytest
	@echo "✅ Development dependencies installed"

# Build package
build: clean
	@echo "🏗️ Building package..."
	$(PYTHON) -m build
	@echo "✅ Package built successfully"
	@ls -la dist/

# Test package locally
test-local: build
	@echo "🧪 Testing package locally..."
	@echo "Creating test environment..."
	$(PYTHON) -m venv test_env
	test_env/bin/pip install dist/*.whl
	@echo "Testing CLI..."
	test_env/bin/ai-code-review --version
	test_env/bin/ai-code-review --help
	@echo "Testing imports..."
	test_env/bin/python -c "from ai_code_reviewer import AICodeReviewer; print('✅ Import successful')"
	@echo "Cleaning up..."
	rm -rf test_env/
	@echo "✅ Local test completed"

# Run test suite
test:
	@echo "🧪 Running test suite..."
	$(PYTHON) -m pytest tests/ -v --cov=ai_code_reviewer
	@echo "✅ Tests completed"

# Lint code
lint:
	@echo "🔍 Running code quality checks..."
	$(PYTHON) -m ruff check ai_code_reviewer/
	$(PYTHON) -m black --check ai_code_reviewer/
	$(PYTHON) -m mypy ai_code_reviewer/
	@echo "✅ Linting completed"

# Security scan  
security:
	@echo "🛡️ Running security scan..."
	$(PYTHON) -m bandit -r ai_code_reviewer/
	@echo "✅ Security scan completed"

# Package validation
validate: build
	@echo "📋 Validating package..."
	$(PYTHON) -m twine check dist/*
	@echo "✅ Package validation completed"

# Run all quality checks
check-all: lint security validate
	@echo "🎯 All quality checks completed"

# Full package validation
validate-all:
	@echo "🔍 Running full package validation..."
	$(PYTHON) validate_package.py
	@echo "✅ Full validation completed"

# Show version
version:
	@echo "📋 Package Information:"
	@echo "Name: $(PACKAGE_NAME)"
	@$(PYTHON) -c "from ai_code_reviewer import __version__; print(f'Version: {__version__}')"
	@echo "Build files:"
	@ls -la dist/ 2>/dev/null || echo "No build files (run 'make build' first)"

# Upload to Test PyPI
upload-test: build validate
	@echo "📤 Uploading to Test PyPI..."
	@echo "⚠️  Make sure TWINE_USERNAME and TWINE_PASSWORD are set for testpypi"
	$(PYTHON) -m twine upload --repository testpypi dist/*
	@echo "✅ Upload to Test PyPI completed"
	@echo "🧪 Test installation: pip install --index-url https://test.pypi.org/simple/ $(PACKAGE_NAME)==$(shell python -c 'from ai_code_reviewer import __version__; print(__version__)')"

# Upload to PyPI  
upload: build validate
	@echo "📤 Uploading to PyPI..."
	@echo "⚠️  Make sure TWINE_USERNAME and TWINE_PASSWORD are set for pypi"
	@read -p "Are you sure you want to upload to PyPI? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(PYTHON) -m twine upload dist/*; \
		echo "✅ Upload to PyPI completed"; \
		echo "🎉 Package available at: https://pypi.org/project/$(PACKAGE_NAME)/"; \
	else \
		echo "❌ Upload cancelled"; \
	fi

# Development workflow
dev-setup: clean install-dev
	@echo "🚀 Development environment ready"

# Full release workflow
release: clean validate-all check-all build upload-test
	@echo "🎯 Release workflow completed"
	@echo "💡 Test the package from Test PyPI before running 'make upload'"

# Quick build and test cycle
quick-test: clean build test-local
	@echo "⚡ Quick build and test completed"

# Show package info
info:
	@echo "📊 Package Information:"
	@echo "========================"
	@$(PYTHON) setup.py --name --version --description
	@echo ""
	@echo "📁 Package structure:"
	@find ai_code_reviewer -name "*.py" | head -10
	@echo ""
	@echo "📦 Dependencies:"
	@grep "install_requires" setup.py -A 10 | grep -E "\".*\""

# Install from PyPI (for testing)
install-pypi:
	@echo "📦 Installing from PyPI..."
	$(PIP) install --upgrade $(PACKAGE_NAME)
	@ai-code-review --version
	@echo "✅ PyPI installation completed"

# Install from Test PyPI
install-test-pypi:
	@echo "📦 Installing from Test PyPI..."
	$(PIP) install --index-url https://test.pypi.org/simple/ --upgrade $(PACKAGE_NAME)
	@ai-code-review --version
	@echo "✅ Test PyPI installation completed"