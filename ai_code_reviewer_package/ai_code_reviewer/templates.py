#!/usr/bin/env python3
"""
Template Manager - Project templates en setup utilities
"""

import os
import shutil
import yaml
from pathlib import Path
from typing import Dict, List


class TemplateManager:
    """Beheert project templates en configuraties."""
    
    def __init__(self):
        self.package_dir = Path(__file__).parent
        self.templates_dir = self.package_dir / "templates"
    
    def get_template_files(self) -> List[str]:
        """Lijst van beschikbare template bestanden."""
        templates = []
        if self.templates_dir.exists():
            for template_file in self.templates_dir.rglob("*"):
                if template_file.is_file():
                    templates.append(str(template_file.relative_to(self.templates_dir)))
        return templates
    
    def install_templates(self, project_root: str) -> bool:
        """Installeer configuration templates in project."""
        project_path = Path(project_root)
        
        try:
            # Copy .pre-commit-config.yaml if it doesn't exist
            precommit_template = self.templates_dir / ".pre-commit-config.yaml"
            precommit_target = project_path / ".pre-commit-config.yaml"
            
            if precommit_template.exists() and not precommit_target.exists():
                shutil.copy2(precommit_template, precommit_target)
                print(f"✅ Installed pre-commit config at {precommit_target}")
            
            # Copy pyproject.toml template if needed
            pyproject_template = self.templates_dir / "pyproject.toml"
            pyproject_target = project_path / "pyproject.toml"
            
            if pyproject_template.exists() and not pyproject_target.exists():
                shutil.copy2(pyproject_template, pyproject_target)
                print(f"✅ Installed pyproject.toml at {pyproject_target}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error installing templates: {e}")
            return False
    
    def setup_git_hooks(self, project_root: str) -> bool:
        """Setup git hooks voor automatische reviews."""
        project_path = Path(project_root)
        hooks_dir = project_path / ".git" / "hooks"
        
        if not hooks_dir.exists():
            print("❌ No git repository found")
            return False
        
        try:
            # Create pre-commit hook
            hook_content = '''#!/bin/sh
# AI Code Review pre-commit hook
# Runs automatic code review before each commit

echo "🤖 Running AI Code Review..."

# Run AI code review
ai-code-review --ai-agent "git-hook"

# Capture exit code
exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo "❌ Code review failed. Fix issues before committing."
    echo "💡 Run 'ai-code-review' manually to see detailed feedback."
    exit $exit_code
fi

echo "✅ Code review passed!"
exit 0
'''
            
            hook_file = hooks_dir / "pre-commit"
            hook_file.write_text(hook_content)
            hook_file.chmod(0o755)  # Make executable
            
            print(f"✅ Installed git pre-commit hook at {hook_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error setting up git hooks: {e}")
            return False
    
    def setup_bmad_integration(self, project_root: str) -> bool:
        """Setup BMAD Method integratie."""
        project_path = Path(project_root)
        bmad_dir = project_path / ".bmad-core"
        
        try:
            # Create .bmad-core directory structure
            (bmad_dir / "tasks").mkdir(parents=True, exist_ok=True)
            (bmad_dir / "config").mkdir(parents=True, exist_ok=True)
            
            # Create execute-code-review task
            task_content = '''# AI Code Review Task voor BMAD

**Doel**: Geautomatiseerde code review uitvoeren met AI integratie

## Instructies voor Agent

1. **Pre-review Setup**:
   - Controleer of alle tools geïnstalleerd zijn (ruff, black, mypy, bandit)
   - Laad project configuratie uit `.ai-review-config.yaml`

2. **Review Uitvoering**:
   ```bash
   ai-code-review --ai-agent "${AI_AGENT_NAME:-bmad-agent}"
   ```

3. **Post-review Acties**:
   - Analyseer review rapport in `review_report.md`
   - Bij blocking issues: stop en vraag om handmatige interventie
   - Bij fixable issues: pas auto-fixes toe en run opnieuw
   - Bij passed review: ga door naar volgende stap

## Expected Output

- ✅ Review rapport gegenereerd
- 🔧 Auto-fixes toegepast waar mogelijk
- 📝 Feedback voor remaining issues
- 🚦 Exit code: 0 voor success, 1 voor failure

## Agent Configuration

Dit task detecteert automatisch welke AI agent het gebruikt:
- Claude Code wordt gedetecteerd als "claude"
- GitHub Copilot wordt gedetecteerd als "copilot"  
- Quinn BMAD agent wordt gedetecteerd als "quinn"
- Fallback naar "bmad-agent"

De agent naam wordt gebruikt voor metrics tracking en specialized feedback.
'''
            
            task_file = bmad_dir / "tasks" / "execute-code-review.md"
            task_file.write_text(task_content, encoding='utf-8')
            
            # Create agent environment setup
            env_content = '''#!/bin/bash
# BMAD Agent Environment Setup voor AI Code Review

# Detect AI agent type
if [[ -n "$CLAUDE_CODE_SESSION" ]]; then
    export AI_AGENT_NAME="claude"
elif [[ -n "$GITHUB_COPILOT_TOKEN" ]]; then
    export AI_AGENT_NAME="copilot"
elif [[ -n "$BMAD_QUINN_ACTIVE" ]]; then
    export AI_AGENT_NAME="quinn"
else
    export AI_AGENT_NAME="bmad-agent"
fi

# Setup review environment
export AI_REVIEW_MODE="bmad"
export AI_REVIEW_INTEGRATION="true"

echo "🎭 BMAD AI Review Environment Ready"
echo "🤖 Agent: $AI_AGENT_NAME"
'''
            
            env_file = bmad_dir / "config" / "agent-environment.sh"
            env_file.write_text(env_content)
            
            # Create init script
            init_content = '''#!/bin/bash
# BMAD Auto-init script for AI Code Review

# Source environment
source .bmad-core/config/agent-environment.sh

# Check if ai-code-review is installed
if ! command -v ai-code-review &> /dev/null; then
    echo "📦 Installing AI Code Review package..."
    pip install ai-code-reviewer
fi

# Create config if not exists
if [ ! -f ".ai-review-config.yaml" ]; then
    echo "⚙️ Creating project config..."
    ai-code-review setup --install-templates
fi

echo "✅ BMAD AI Code Review ready!"
echo "💡 Use: *execute-code-review"
'''
            
            init_file = bmad_dir / "init.sh"
            init_file.write_text(init_content)
            init_file.chmod(0o755)
            
            print(f"✅ BMAD integration setup at {bmad_dir}")
            print("💡 Agents can now use '*execute-code-review' command")
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up BMAD integration: {e}")
            return False
    
    def create_framework_config(self, project_root: str, framework: str) -> Dict:
        """Maak framework-specifieke configuratie."""
        base_config = {
            'max_iterations': 5,
            'custom_checks': True,
            'framework': framework,
        }
        
        if framework == 'django':
            base_config.update({
                'source_dirs': ['.'],
                'custom_check_types': ['sql_safety', 'django_patterns'],
                'docstring_language': 'english'
            })
        elif framework == 'flask':
            base_config.update({
                'source_dirs': ['.'],
                'custom_check_types': ['sql_safety', 'flask_patterns'],
                'docstring_language': 'english'
            })
        elif framework == 'streamlit':
            base_config.update({
                'source_dirs': ['src/'],
                'custom_check_types': ['sql_safety', 'streamlit_patterns'],
                'docstring_language': 'dutch'
            })
        else:  # generic
            base_config.update({
                'source_dirs': ['src/', '.'],
                'custom_check_types': ['sql_safety'],
                'docstring_language': 'english'
            })
            
        return base_config