#!/usr/bin/env python3
"""
Validation Dashboard Status Updater

Dit script kan de status van componenten in het validation dashboard updaten
door echte tests uit te voeren en de resultaten te rapporteren.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add src to path for imports
sys.path.append("src")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationStatusChecker:
    """Controleert de status van alle validatie service componenten."""

    def __init__(self):
        self.status_data = {
            "last_updated": None,
            "components": {},
            "test_results": {},
            "connections": {},
            "overall_health": "unknown",
        }

    async def check_modular_validation_service(self) -> dict[str, Any]:
        """Test de ModularValidationService."""
        try:
            from services.validation.config import ValidationConfig
            from services.validation.modular_validation_service import (
                ModularValidationService,
            )

            # Test configuratie laden
            config_path = Path("src/config/validation_rules.yaml")
            if not config_path.exists():
                return {"status": "error", "message": "Config file not found"}

            config = ValidationConfig.from_yaml(str(config_path))
            service = ModularValidationService(None, None, config)

            # Test basis functionaliteit
            result = await service.validate_definition(
                "test", "Dit is een test definitie voor validatie"
            )

            return {
                "status": "working",
                "message": "Service operational",
                "test_score": result.get("overall_score", 0),
                "rules_tested": len(result.get("passed_rules", []))
                + len(result.get("violations", [])),
                "violations": len(result.get("violations", [])),
            }

        except Exception as e:
            logger.error(f"ModularValidationService test failed: {e}")
            return {"status": "error", "message": str(e)}

    async def check_validation_config(self) -> dict[str, Any]:
        """Test de ValidationConfig."""
        try:
            from services.validation.config import ValidationConfig

            config_path = Path("src/config/validation_rules.yaml")
            if not config_path.exists():
                return {"status": "error", "message": "Config file not found"}

            config = ValidationConfig.from_yaml(str(config_path))

            return {
                "status": "working",
                "message": "Config loaded successfully",
                "rules_count": len(config.weights),
                "threshold": config.thresholds.get("overall_accept", 0.75),
            }

        except Exception as e:
            logger.error(f"ValidationConfig test failed: {e}")
            return {"status": "error", "message": str(e)}

    async def check_container_integration(self) -> dict[str, Any]:
        """Test de container integratie."""
        try:
            from services.container import ServiceContainer

            container = ServiceContainer()
            orchestrator = container.orchestrator()

            # Check if orchestrator has validation service
            has_validation = hasattr(orchestrator, "validation_service")

            return {
                "status": "working" if has_validation else "partial",
                "message": "Container integration functional",
                "has_validation_service": has_validation,
            }

        except Exception as e:
            logger.error(f"Container integration test failed: {e}")
            return {"status": "error", "message": str(e)}

    async def check_toetsregel_manager_connection(self) -> dict[str, Any]:
        """Test de ToetsregelManager connectie."""
        try:
            from toetsregels.manager import ToetsregelManager

            manager = ToetsregelManager()

            # Try to load some rules
            try:
                rules = manager.get_all_regels()
                return {
                    "status": "working",
                    "message": "ToetsregelManager operational",
                    "rules_available": len(rules) if rules else 0,
                }
            except Exception:
                return {
                    "status": "partial",
                    "message": "ToetsregelManager exists but rules not loaded",
                    "rules_available": 0,
                }

        except Exception as e:
            logger.error(f"ToetsregelManager test failed: {e}")
            return {"status": "error", "message": str(e)}

    async def run_test_suite(self) -> dict[str, Any]:
        """Voer de basis test suite uit."""
        try:
            import subprocess

            # Run contract tests
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "pytest",
                    "tests/services/test_modular_validation_service_contract.py",
                    "-v",
                    "--tb=short",
                ],
                capture_output=True,
                text=True,
                cwd=".",
                check=False,
            )

            if result.returncode == 0:
                return {
                    "status": "working",
                    "message": "Contract tests passed",
                    "output": result.stdout[-500:],  # Last 500 chars
                }
            else:
                return {
                    "status": "error",
                    "message": "Contract tests failed",
                    "output": result.stderr[-500:],
                }

        except Exception as e:
            logger.error(f"Test suite execution failed: {e}")
            return {"status": "error", "message": str(e)}

    async def check_all_components(self) -> dict[str, Any]:
        """Controleer alle componenten."""
        logger.info("Starting comprehensive component check...")

        checks = {
            "modular_validation_service": self.check_modular_validation_service(),
            "validation_config": self.check_validation_config(),
            "container_integration": self.check_container_integration(),
            "toetsregel_manager": self.check_toetsregel_manager_connection(),
            "test_suite": self.run_test_suite(),
        }

        # Run all checks concurrently
        results = {}
        for name, check in checks.items():
            try:
                results[name] = await check
                logger.info(f"✅ {name}: {results[name]['status']}")
            except Exception as e:
                results[name] = {"status": "error", "message": str(e)}
                logger.error(f"❌ {name}: {e}")

        # Determine overall health
        working_count = sum(1 for r in results.values() if r["status"] == "working")
        total_count = len(results)

        if working_count == total_count:
            overall_health = "healthy"
        elif working_count > total_count / 2:
            overall_health = "partial"
        else:
            overall_health = "unhealthy"

        self.status_data.update(
            {
                "last_updated": datetime.now().isoformat(),
                "components": results,
                "overall_health": overall_health,
                "health_score": round((working_count / total_count) * 100, 1),
            }
        )

        return self.status_data

    def save_status(self, filename: str = "validation-status.json"):
        """Bewaar de status naar een JSON bestand."""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.status_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Status saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save status: {e}")

    def generate_status_report(self) -> str:
        """Genereer een tekstueel status rapport."""
        report = []
        report.append("=" * 60)
        report.append("VALIDATION SERVICE V2 STATUS REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {self.status_data.get('last_updated', 'Unknown')}")
        report.append(
            f"Overall Health: {self.status_data.get('overall_health', 'Unknown').upper()}"
        )
        report.append(f"Health Score: {self.status_data.get('health_score', 0)}%")
        report.append("")

        components = self.status_data.get("components", {})
        for name, status in components.items():
            status_icon = {"working": "✅", "partial": "⚠️", "error": "❌"}.get(
                status["status"], "❓"
            )

            report.append(f"{status_icon} {name.replace('_', ' ').title()}")
            report.append(f"   Status: {status['status'].upper()}")
            report.append(f"   Message: {status['message']}")

            # Add specific metrics if available
            if "test_score" in status:
                report.append(f"   Test Score: {status['test_score']}")
            if "rules_count" in status:
                report.append(f"   Rules Count: {status['rules_count']}")
            if "rules_available" in status:
                report.append(f"   Rules Available: {status['rules_available']}")

            report.append("")

        return "\n".join(report)


async def main():
    """Hoofdfunctie voor status controle."""
    checker = ValidationStatusChecker()

    print("🔍 Starting Validation Service V2 Health Check...")
    print("=" * 60)

    # Run comprehensive check
    status = await checker.check_all_components()

    # Save results
    checker.save_status("validation-status.json")

    # Generate and print report
    report = checker.generate_status_report()
    print(report)

    # Save report to file
    with open("validation-status-report.txt", "w", encoding="utf-8") as f:
        f.write(report)

    print("=" * 60)
    print("📊 Results saved to:")
    print("   - validation-status.json (machine readable)")
    print("   - validation-status-report.txt (human readable)")

    # Exit with error code if unhealthy
    if status["overall_health"] == "unhealthy":
        print("❌ System is unhealthy")
        sys.exit(1)
    elif status["overall_health"] == "partial":
        print("⚠️ System has issues")
        sys.exit(2)
    else:
        print("✅ System is healthy")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
