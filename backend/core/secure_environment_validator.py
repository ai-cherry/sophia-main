"""Secure Environment Variable Validator
Validates and manages environment variables with security checks
"""

import logging
import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SecretType(Enum):
    """Types of secrets for validation"""

    API_KEY = "api_key"
    PASSWORD = "password"
    TOKEN = "token"
    URL = "url"
    DATABASE = "database"
    SSH_KEY = "ssh_key"
    CERTIFICATE = "certificate"


@dataclass
class ValidationRule:
    """Validation rule for environment variables"""

    name: str
    required: bool = True
    secret_type: Optional[SecretType] = None
    pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    allowed_values: Optional[List[str]] = None
    description: str = ""


class SecureEnvironmentValidator:
    """Validates environment variables with security checks
    Ensures all required secrets are present and properly formatted
    """

    def __init__(self):
        """Initialize validator with security rules"""
        self.validation_rules = self._define_validation_rules()
        self.validation_results: Dict[str, Any] = {}

    def _define_validation_rules(self) -> Dict[str, ValidationRule]:
        """Define validation rules for all environment variables"""
        rules = {
            # Core Application
            "SECRET_KEY": ValidationRule(
                name="SECRET_KEY",
                required=True,
                secret_type=SecretType.PASSWORD,
                min_length=32,
                description="Application secret key for encryption",
            ),
            "JWT_SECRET": ValidationRule(
                name="JWT_SECRET",
                required=True,
                secret_type=SecretType.PASSWORD,
                min_length=32,
                description="JWT signing secret",
            ),
            # Database
            "POSTGRES_HOST": ValidationRule(
                name="POSTGRES_HOST", required=True, description="PostgreSQL host"
            ),
            "POSTGRES_USER": ValidationRule(
                name="POSTGRES_USER", required=True, description="PostgreSQL username"
            ),
            "POSTGRES_PASSWORD": ValidationRule(
                name="POSTGRES_PASSWORD",
                required=True,
                secret_type=SecretType.PASSWORD,
                min_length=8,
                description="PostgreSQL password",
            ),
            "POSTGRES_DB": ValidationRule(
                name="POSTGRES_DB",
                required=True,
                description="PostgreSQL database name",
            ),
            # AI Services
            "OPENAI_API_KEY": ValidationRule(
                name="OPENAI_API_KEY",
                required=False,
                secret_type=SecretType.API_KEY,
                pattern=r"^sk-[a-zA-Z0-9]{48}$",
                description="OpenAI API key",
            ),
            "ANTHROPIC_API_KEY": ValidationRule(
                name="ANTHROPIC_API_KEY",
                required=False,
                secret_type=SecretType.API_KEY,
                pattern=r"^sk-ant-api03-[a-zA-Z0-9_-]{95}$",
                description="Anthropic Claude API key",
            ),
            # Vector Databases
            "PINECONE_API_KEY": ValidationRule(
                name="PINECONE_API_KEY",
                required=False,
                secret_type=SecretType.API_KEY,
                pattern=r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$",
                description="Pinecone API key",
            ),
            "WEAVIATE_API_KEY": ValidationRule(
                name="WEAVIATE_API_KEY",
                required=False,
                secret_type=SecretType.API_KEY,
                description="Weaviate API key",
            ),
            # Business Integrations
            "GONG_API_KEY": ValidationRule(
                name="GONG_API_KEY",
                required=False,
                secret_type=SecretType.API_KEY,
                description="Gong API key",
            ),
            "GONG_API_SECRET": ValidationRule(
                name="GONG_API_SECRET",
                required=False,
                secret_type=SecretType.API_KEY,
                description="Gong API secret",
            ),
            "HUBSPOT_API_KEY": ValidationRule(
                name="HUBSPOT_API_KEY",
                required=False,
                secret_type=SecretType.API_KEY,
                description="HubSpot API key",
            ),
            "SALESFORCE_PASSWORD": ValidationRule(
                name="SALESFORCE_PASSWORD",
                required=False,
                secret_type=SecretType.PASSWORD,
                description="Salesforce password",
            ),
            "SALESFORCE_SECURITY_TOKEN": ValidationRule(
                name="SALESFORCE_SECURITY_TOKEN",
                required=False,
                secret_type=SecretType.TOKEN,
                description="Salesforce security token",
            ),
            # Slack
            "SLACK_BOT_TOKEN": ValidationRule(
                name="SLACK_BOT_TOKEN",
                required=False,
                secret_type=SecretType.TOKEN,
                pattern=r"^xoxb-[0-9]+-[0-9]+-[a-zA-Z0-9]+$",
                description="Slack bot token",
            ),
            "SLACK_APP_TOKEN": ValidationRule(
                name="SLACK_APP_TOKEN",
                required=False,
                secret_type=SecretType.TOKEN,
                pattern=r"^xapp-[0-9]+-[a-zA-Z0-9]+-[a-zA-Z0-9]+$",
                description="Slack app token",
            ),
            "SLACK_SIGNING_SECRET": ValidationRule(
                name="SLACK_SIGNING_SECRET",
                required=False,
                secret_type=SecretType.API_KEY,
                min_length=32,
                max_length=32,
                description="Slack signing secret",
            ),
            # Cloud Services
            "LAMBDA_LABS_API_KEY": ValidationRule(
                name="LAMBDA_LABS_API_KEY",
                required=False,
                secret_type=SecretType.API_KEY,
                description="Lambda Labs API key",
            ),
            "VERCEL_ACCESS_TOKEN": ValidationRule(
                name="VERCEL_ACCESS_TOKEN",
                required=False,
                secret_type=SecretType.TOKEN,
                description="Vercel access token",
            ),
            "PULUMI_ACCESS_TOKEN": ValidationRule(
                name="PULUMI_ACCESS_TOKEN",
                required=True,
                secret_type=SecretType.TOKEN,
                description="Pulumi access token",
            ),
            # Snowflake
            "SNOWFLAKE_ACCOUNT": ValidationRule(
                name="SNOWFLAKE_ACCOUNT",
                required=False,
                description="Snowflake account identifier",
            ),
            "SNOWFLAKE_USER": ValidationRule(
                name="SNOWFLAKE_USER", required=False, description="Snowflake username"
            ),
            "SNOWFLAKE_PASSWORD": ValidationRule(
                name="SNOWFLAKE_PASSWORD",
                required=False,
                secret_type=SecretType.PASSWORD,
                min_length=8,
                description="Snowflake password",
            ),
            # Environment Configuration
            "ENVIRONMENT": ValidationRule(
                name="ENVIRONMENT",
                required=True,
                allowed_values=["development", "staging", "production"],
                description="Application environment",
            ),
            "DEBUG": ValidationRule(
                name="DEBUG",
                required=False,
                allowed_values=["true", "false", "True", "False", "1", "0"],
                description="Debug mode flag",
            ),
        }

        return rules

    def validate_environment(
        self, env_vars: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Validate all environment variables"""
        if env_vars is None:
            env_vars = dict(os.environ)

        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "missing_required": [],
            "invalid_format": [],
            "security_issues": [],
            "summary": {},
        }

        # Check each validation rule
        for rule_name, rule in self.validation_rules.items():
            value = env_vars.get(rule_name)
            validation_result = self._validate_single_var(rule, value)

            if not validation_result["valid"]:
                results["valid"] = False

                if validation_result["missing_required"]:
                    results["missing_required"].append(rule_name)
                    results["errors"].append(f"Missing required variable: {rule_name}")

                if validation_result["invalid_format"]:
                    results["invalid_format"].append(rule_name)
                    results["errors"].append(
                        f"Invalid format for {rule_name}: {validation_result['error']}"
                    )

                if validation_result["security_issue"]:
                    results["security_issues"].append(rule_name)
                    results["warnings"].append(
                        f"Security issue with {rule_name}: {validation_result['error']}"
                    )

        # Check for hardcoded secrets
        hardcoded_secrets = self._check_hardcoded_secrets(env_vars)
        if hardcoded_secrets:
            results["valid"] = False
            results["security_issues"].extend(hardcoded_secrets)
            for secret in hardcoded_secrets:
                results["errors"].append(f"Hardcoded secret detected: {secret}")

        # Generate summary
        results["summary"] = {
            "total_variables": len(env_vars),
            "validated_variables": len(self.validation_rules),
            "required_missing": len(results["missing_required"]),
            "format_errors": len(results["invalid_format"]),
            "security_issues": len(results["security_issues"]),
            "overall_status": "PASS" if results["valid"] else "FAIL",
        }

        self.validation_results = results
        return results

    def _validate_single_var(
        self, rule: ValidationRule, value: Optional[str]
    ) -> Dict[str, Any]:
        """Validate a single environment variable"""
        result = {
            "valid": True,
            "missing_required": False,
            "invalid_format": False,
            "security_issue": False,
            "error": None,
        }

        # Check if required variable is missing
        if rule.required and not value:
            result["valid"] = False
            result["missing_required"] = True
            result["error"] = f"Required variable {rule.name} is missing"
            return result

        # Skip validation if optional and not provided
        if not rule.required and not value:
            return result

        # Validate pattern
        if rule.pattern and value:
            if not re.match(rule.pattern, value):
                result["valid"] = False
                result["invalid_format"] = True
                result["error"] = "Value does not match required pattern"
                return result

        # Validate length
        if value:
            if rule.min_length and len(value) < rule.min_length:
                result["valid"] = False
                result["invalid_format"] = True
                result["error"] = (
                    f"Value too short (minimum {rule.min_length} characters)"
                )
                return result

            if rule.max_length and len(value) > rule.max_length:
                result["valid"] = False
                result["invalid_format"] = True
                result["error"] = (
                    f"Value too long (maximum {rule.max_length} characters)"
                )
                return result

        # Validate allowed values
        if rule.allowed_values and value:
            if value not in rule.allowed_values:
                result["valid"] = False
                result["invalid_format"] = True
                result["error"] = (
                    f"Value must be one of: {', '.join(rule.allowed_values)}"
                )
                return result

        # Security checks for secrets
        if rule.secret_type and value:
            security_check = self._check_secret_security(
                rule.name, value, rule.secret_type
            )
            if not security_check["secure"]:
                result["security_issue"] = True
                result["error"] = security_check["issue"]

        return result

    def _check_secret_security(
        self, name: str, value: str, secret_type: SecretType
    ) -> Dict[str, Any]:
        """Check security of secret values"""
        result = {"secure": True, "issue": None}

        # Check for common insecure patterns
        insecure_patterns = [
            "password123",
            "admin",
            "test",
            "demo",
            "example",
            "changeme",
            "default",
        ]

        value_lower = value.lower()
        for pattern in insecure_patterns:
            if pattern in value_lower:
                result["secure"] = False
                result["issue"] = f"Contains insecure pattern: {pattern}"
                return result

        # Check for repeated characters (weak passwords)
        if secret_type in [SecretType.PASSWORD, SecretType.API_KEY]:
            if len(set(value)) < len(value) * 0.5:  # Less than 50% unique characters
                result["secure"] = False
                result["issue"] = "Too many repeated characters"
                return result

        # Check for sequential patterns
        if secret_type == SecretType.PASSWORD:
            sequential_patterns = ["123", "abc", "qwe", "asd"]
            for pattern in sequential_patterns:
                if pattern in value_lower:
                    result["secure"] = False
                    result["issue"] = f"Contains sequential pattern: {pattern}"
                    return result

        return result

    def _check_hardcoded_secrets(self, env_vars: Dict[str, str]) -> List[str]:
        """Check for hardcoded secrets that should not be in environment variables"""
        hardcoded_secrets = []

        # Known hardcoded values that should be replaced
        hardcoded_patterns = {
            "your_api_key_here": "placeholder",
            "your_secret_here": "placeholder",
            "changeme": "placeholder",
            "admin123": "placeholder",
            "password123": "placeholder",
            "secret123": "placeholder",
        }

        for var_name, var_value in env_vars.items():
            if var_value:
                for pattern, issue_type in hardcoded_patterns.items():
                    if pattern in var_value:
                        hardcoded_secrets.append(f"{var_name} contains {issue_type}")

        return hardcoded_secrets

    def generate_secure_env_template(self) -> str:
        """Generate a secure .env template"""
        template_lines = [
            "# SOPHIA AI System - Secure Environment Variables",
            "# Copy this file to .env and fill in your secure values",
            "# DO NOT commit .env files to version control",
            "",
        ]

        # Group rules by category
        categories = {
            "Core Application": ["SECRET_KEY", "JWT_SECRET", "ENVIRONMENT", "DEBUG"],
            "Database": [
                "POSTGRES_HOST",
                "POSTGRES_USER",
                "POSTGRES_PASSWORD",
                "POSTGRES_DB",
            ],
            "AI Services": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"],
            "Vector Databases": ["PINECONE_API_KEY", "WEAVIATE_API_KEY"],
            "Business Integrations": [
                "GONG_API_KEY",
                "GONG_API_SECRET",
                "HUBSPOT_API_KEY",
            ],
            "Slack": ["SLACK_BOT_TOKEN", "SLACK_APP_TOKEN", "SLACK_SIGNING_SECRET"],
            "Cloud Services": [
                "LAMBDA_LABS_API_KEY",
                "VERCEL_ACCESS_TOKEN",
                "PULUMI_ACCESS_TOKEN",
            ],
            "Snowflake": ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD"],
        }

        for category, var_names in categories.items():
            template_lines.append(f"# {category}")
            for var_name in var_names:
                rule = self.validation_rules.get(var_name)
                if rule:
                    required_marker = " (REQUIRED)" if rule.required else " (OPTIONAL)"
                    template_lines.append(f"# {rule.description}{required_marker}")

                    if rule.secret_type:
                        template_lines.append(
                            f"{var_name}=your_secure_{var_name.lower()}_here"
                        )
                    else:
                        template_lines.append(
                            f"{var_name}=your_{var_name.lower()}_here"
                        )

                    template_lines.append("")

        return "\n".join(template_lines)

    def get_validation_summary(self) -> str:
        """Get a human-readable validation summary"""
        if not self.validation_results:
            return "No validation results available. Run validate_environment() first."

        summary = self.validation_results["summary"]
        lines = [
            "🔒 SOPHIA AI ENVIRONMENT VALIDATION SUMMARY",
            "=" * 50,
            f"Overall Status: {summary['overall_status']}",
            f"Total Variables: {summary['total_variables']}",
            f"Validated Variables: {summary['validated_variables']}",
            f"Required Missing: {summary['required_missing']}",
            f"Format Errors: {summary['format_errors']}",
            f"Security Issues: {summary['security_issues']}",
            "",
        ]

        if self.validation_results["errors"]:
            lines.append("🚨 ERRORS:")
            for error in self.validation_results["errors"]:
                lines.append(f"  - {error}")
            lines.append("")

        if self.validation_results["warnings"]:
            lines.append("⚠️  WARNINGS:")
            for warning in self.validation_results["warnings"]:
                lines.append(f"  - {warning}")
            lines.append("")

        if summary["overall_status"] == "PASS":
            lines.append("✅ Environment validation passed!")
        else:
            lines.append(
                "❌ Environment validation failed. Please fix the issues above."
            )

        return "\n".join(lines)


# Convenience functions
def validate_sophia_environment() -> Dict[str, Any]:
    """Validate Sophia AI environment variables"""
    validator = SecureEnvironmentValidator()
    return validator.validate_environment()


def generate_secure_env_file(output_path: str = ".env.secure.example") -> str:
    """Generate a secure environment file template"""
    validator = SecureEnvironmentValidator()
    template = validator.generate_secure_env_template()

    with open(output_path, "w") as f:
        f.write(template)

    return output_path


if __name__ == "__main__":
    # Test the validator
    validator = SecureEnvironmentValidator()
    results = validator.validate_environment()
    print(validator.get_validation_summary())

    # Generate secure template
    template_path = generate_secure_env_file()
    print(f"\nSecure environment template generated: {template_path}")
