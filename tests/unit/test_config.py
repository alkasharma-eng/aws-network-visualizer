"""
Unit tests for configuration module.
"""

import pytest
from pydantic import ValidationError

from src.core.config import Settings


class TestSettings:
    """Test Settings class."""

    def test_default_settings(self):
        """Test default settings values."""
        settings = Settings()

        assert settings.app_name == "aws-network-visualizer"
        assert settings.aws_region == "us-east-1"
        assert settings.enable_xray is True
        assert settings.enable_metrics is True

    def test_environment_validation(self):
        """Test environment validation."""
        with pytest.raises(ValidationError):
            Settings(environment="invalid")

        # Valid environments
        for env in ["development", "staging", "production"]:
            settings = Settings(environment=env)
            assert settings.environment == env

    def test_log_level_validation(self):
        """Test log level validation."""
        with pytest.raises(ValidationError):
            Settings(log_level="INVALID")

        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings = Settings(log_level=level)
            assert settings.log_level == level

    def test_bedrock_region_default(self):
        """Test Bedrock region defaults to AWS region."""
        settings = Settings(aws_region="us-west-2")
        assert settings.get_bedrock_region() == "us-west-2"

        settings = Settings(aws_region="us-east-1", bedrock_region="us-west-2")
        assert settings.get_bedrock_region() == "us-west-2"

    def test_is_production(self):
        """Test production environment detection."""
        settings = Settings(environment="production")
        assert settings.is_production() is True
        assert settings.is_development() is False

        settings = Settings(environment="development")
        assert settings.is_production() is False
        assert settings.is_development() is True
