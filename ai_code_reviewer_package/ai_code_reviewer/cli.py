#!/usr/bin/env python3
"""
AI Code Reviewer CLI Interface
Command-line interface voor het AI Code Review package
"""

import argparse
import asyncio
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, Optional

from .core import AICodeReviewer
from .updater import PackageUpdater
from .templates import TemplateManager


def load_config(config_path: Optional[str] = None) -> Dict:
    """Laad configuratie van bestand of gebruik defaults."""
    default_config = {
        'max_iterations': 5,
        'source_dirs': ['src/'],
        'custom_checks': True,
        'docstring_language': 'dutch',
        'framework': 'streamlit',
        'custom_check_types': ['sql_safety', 'docstring_language', 'framework_patterns'],
        'false_positive_filters': [
            'logger.', 'log.', 'print(', 'st.success', 'st.error', 'st.info',
            'st.write', 'st.markdown', 'errors.append', 'message=f"', 'raise'
        ]
    }
    
    if config_path and Path(config_path).exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)
        except Exception as e:
            print(f"Warning: Could not load config from {config_path}: {e}")
    
    return default_config


def create_project_config(project_root: str) -> None:
    """Maak een project-specifieke configuratie."""
    config_path = Path(project_root) / '.ai-review-config.yaml'
    
    if config_path.exists():
        print(f"Config already exists at {config_path}")
        return
    
    # Detect project type
    project_path = Path(project_root)
    framework = 'generic'
    source_dirs = ['src/']
    
    if (project_path / 'manage.py').exists():
        framework = 'django'
        source_dirs = ['.']
    elif (project_path / 'app.py').exists() or (project_path / 'flask_app.py').exists():
        framework = 'flask'
        source_dirs = ['.']
    elif any((project_path / 'src').rglob('*streamlit*')):
        framework = 'streamlit'
        source_dirs = ['src/']
    elif (project_path / 'src').exists():
        source_dirs = ['src/']
    elif (project_path / 'app').exists():
        source_dirs = ['app/']
    else:
        source_dirs = ['.']
    
    config = {
        'max_iterations': 5,
        'source_dirs': source_dirs,
        'custom_checks': True,
        'docstring_language': 'english',  # Default to English for broader use
        'framework': framework,
        'custom_check_types': ['sql_safety', 'framework_patterns'],
        'false_positive_filters': [
            'logger.', 'log.', 'print(',
            'errors.append', 'message=f"', 'raise'
        ]
    }
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        print(f"✅ Created config file at {config_path}")
        print(f"📝 Detected framework: {framework}")
        print(f"📁 Source directories: {source_dirs}")
    except Exception as e:
        print(f"Error creating config: {e}")


def cmd_review(args):
    """Hoofdcommando: run code review (v2.0.0 met BMAD integratie)."""
    config = load_config(args.config)
    
    # Override config with command line args
    if args.max_iterations:
        config['max_iterations'] = args.max_iterations
    if args.source_dirs:
        config['source_dirs'] = args.source_dirs
    if args.framework:
        config['framework'] = args.framework
    
    # Set environment variable for tracking
    os.environ['AI_AGENT_NAME'] = args.ai_agent
    
    reviewer = AICodeReviewer(
        max_iterations=config['max_iterations'],
        project_root=args.project_root,
        config=config,
        ai_agent=args.ai_agent
    )
    
    # Check BMAD integration status
    if reviewer.bmad_integration_enabled:
        print("🎭 BMAD environment detected")
        reviewer.setup_bmad_integration()
    
    # Run the review cycle
    result = asyncio.run(reviewer.run_review_cycle())
    
    # Exit with appropriate code
    sys.exit(0 if result.passed else 1)


def cmd_setup(args):
    """Setup commando: configureer project voor AI review."""
    template_manager = TemplateManager()
    
    print("🚀 Setting up AI Code Review for your project...")
    
    # Create config
    create_project_config(args.project_root)
    
    # Install templates
    if args.install_templates:
        template_manager.install_templates(args.project_root)
    
    # Setup git hooks
    if args.setup_hooks:
        template_manager.setup_git_hooks(args.project_root)
    
    print("✅ AI Code Review setup completed!")


def cmd_update(args):
    """Update commando: update het package naar latest versie."""
    updater = PackageUpdater()
    
    if args.check_only:
        latest_version = updater.check_for_updates()
        if latest_version:
            print(f"📦 New version available: {latest_version}")
        else:
            print("✅ You're using the latest version")
    else:
        success = updater.update_package()
        if success:
            print("✅ Package updated successfully!")
        else:
            print("❌ Update failed. Check your internet connection.")


def cmd_init_bmad(args):
    """BMAD integratie setup."""
    template_manager = TemplateManager()
    
    print("🎭 Setting up BMAD integration...")
    success = template_manager.setup_bmad_integration(args.project_root)
    
    if success:
        print("✅ BMAD integration configured!")
        print("💡 Use '*execute-code-review' in BMAD to run reviews")
    else:
        print("❌ BMAD setup failed")

def cmd_test_hook(args):
    """Test BMAD post-edit hook functionaliteit."""
    config = load_config(args.config)
    
    reviewer = AICodeReviewer(
        project_root=args.project_root,
        config=config,
        ai_agent=args.ai_agent
    )
    
    if not reviewer.bmad_integration_enabled:
        print("❌ BMAD environment not detected")
        sys.exit(1)
        
    print(f"🧪 Testing BMAD post-edit hook for agent: {args.ai_agent}")
    
    # Setup BMAD integration
    setup_success = reviewer.setup_bmad_integration()
    if not setup_success:
        print("❌ BMAD setup failed")
        sys.exit(1)
    
    # Trigger the hook
    exit_code = reviewer.trigger_bmad_hook(
        agent_name=args.ai_agent,
        files_changed="test_files"
    )
    
    if exit_code == 0:
        print("✅ BMAD post-edit hook test completed successfully")
    else:
        print("⚠️  BMAD post-edit hook completed with issues")
    
    sys.exit(exit_code)


def main():
    """Hoofdfunctie voor CLI interface."""
    parser = argparse.ArgumentParser(
        description='AI Code Reviewer - Automated code review with AI integration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ai-code-review                    # Run review in current directory
  ai-code-review --max-iterations 3 # Run with max 3 iterations
  ai-code-review setup             # Setup project for AI review
  ai-code-review update            # Update to latest version
  ai-code-review init-bmad         # Setup BMAD integration
        """
    )
    
    # Global arguments
    parser.add_argument('--project-root', type=str, default='.',
                       help='Project root directory (default: current directory)')
    parser.add_argument('--config', type=str, 
                       help='Path to config file (.ai-review-config.yaml)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Review command (default)
    review_parser = subparsers.add_parser('review', help='Run code review (default)')
    review_parser.add_argument('--max-iterations', type=int,
                             help='Maximum number of review iterations')
    review_parser.add_argument('--source-dirs', nargs='+',
                             help='Source directories to check')
    review_parser.add_argument('--framework', type=str,
                             choices=['streamlit', 'django', 'flask', 'generic'],
                             help='Target framework for custom checks')
    review_parser.add_argument('--ai-agent', type=str, default='manual',
                             help='AI agent name for tracking')
    review_parser.set_defaults(func=cmd_review)
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Setup project for AI review')
    setup_parser.add_argument('--install-templates', action='store_true',
                            help='Install configuration templates')
    setup_parser.add_argument('--setup-hooks', action='store_true',
                            help='Setup git hooks')
    setup_parser.set_defaults(func=cmd_setup)
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update package')
    update_parser.add_argument('--check-only', action='store_true',
                             help='Only check for updates, don\'t install')
    update_parser.set_defaults(func=cmd_update)
    
    # BMAD integration command
    bmad_parser = subparsers.add_parser('init-bmad', help='Setup BMAD integration')
    bmad_parser.set_defaults(func=cmd_init_bmad)
    
    # BMAD hook test command
    hook_parser = subparsers.add_parser('test-hook', help='Test BMAD post-edit hook')
    hook_parser.add_argument('--ai-agent', type=str, default='TestAgent',
                           help='AI agent name for hook test')
    hook_parser.set_defaults(func=cmd_test_hook)
    
    args = parser.parse_args()
    
    # If no subcommand, default to review
    if not hasattr(args, 'func'):
        args.func = cmd_review
        args.max_iterations = None
        args.source_dirs = None
        args.framework = None
        args.ai_agent = 'manual'
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()