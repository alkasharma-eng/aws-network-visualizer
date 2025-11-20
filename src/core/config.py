"""
Configuration management using Pydantic Settings.

This module provides type-safe configuration management with support for
environment variables, multiple environments, and validation.
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with environment variable support.

    All settings can be overridden via environment variables with the prefix AWS_NET_VIZ_.
    Example: AWS_NET_VIZ_AWS_REGION=us-west-2
    """

    # Application settings
    app_name: str = Field(default="aws-network-visualizer", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: str = Field(default="development", description="Environment (development, staging, production)")
    debug: bool = Field(default=False, description="Enable debug mode")

    # AWS settings
    aws_region: str = Field(default="us-east-1", description="Primary AWS region")
    aws_profile: Optional[str] = Field(default=None, description="AWS CLI profile name")
    aws_regions: List[str] = Field(
        default_factory=lambda: ["us-east-1"],
        description="List of AWS regions to scan"
    )

    # Observability settings
    enable_xray: bool = Field(default=True, description="Enable AWS X-Ray tracing")
    enable_metrics: bool = Field(default=True, description="Enable CloudWatch metrics")
    enable_structured_logging: bool = Field(default=True, description="Enable structured JSON logging")
    log_level: str = Field(default="INFO", description="Logging level")

    # CloudWatch settings
    cloudwatch_namespace: str = Field(
        default="AWS/NetworkVisualizer",
        description="CloudWatch namespace for metrics"
    )
    cloudwatch_log_group: str = Field(
        default="/aws/network-visualizer",
        description="CloudWatch log group name"
    )

    # Performance settings
    max_concurrent_collectors: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum concurrent resource collectors"
    )
    api_call_timeout: int = Field(
        default=30,
        ge=5,
        le=300,
        description="AWS API call timeout in seconds"
    )
    max_retry_attempts: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts for failed API calls"
    )
    retry_base_delay: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Base delay for exponential backoff in seconds"
    )

    # Storage settings
    dynamodb_table_name: str = Field(
        default="network-visualizer-topology",
        description="DynamoDB table name for topology data"
    )
    s3_bucket_name: Optional[str] = Field(
        default=None,
        description="S3 bucket name for visualizations and archives"
    )
    elasticache_endpoint: Optional[str] = Field(
        default=None,
        description="ElastiCache Redis endpoint"
    )
    cache_ttl_seconds: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Cache TTL in seconds"
    )

    # AI Analysis settings
    enable_ai_analysis: bool = Field(default=True, description="Enable Bedrock AI analysis")
    bedrock_model_id: str = Field(
        default="anthropic.claude-3-5-sonnet-20241022-v2:0",
        description="Bedrock model ID for AI analysis"
    )
    bedrock_region: Optional[str] = Field(
        default=None,
        description="Bedrock region (defaults to aws_region if not set)"
    )
    ai_analysis_max_tokens: int = Field(
        default=4096,
        ge=100,
        le=100000,
        description="Maximum tokens for AI analysis"
    )
    ai_analysis_temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Temperature for AI analysis"
    )

    # Visualization settings
    default_output_format: str = Field(
        default="png",
        description="Default output format (png, svg, html)"
    )
    visualization_width: int = Field(
        default=1920,
        ge=800,
        le=4096,
        description="Visualization width in pixels"
    )
    visualization_height: int = Field(
        default=1080,
        ge=600,
        le=4096,
        description="Visualization height in pixels"
    )

    # Resource collection settings
    collect_vpcs: bool = Field(default=True, description="Collect VPC resources")
    collect_subnets: bool = Field(default=True, description="Collect Subnet resources")
    collect_ec2_instances: bool = Field(default=True, description="Collect EC2 instances")
    collect_internet_gateways: bool = Field(default=True, description="Collect Internet Gateways")
    collect_nat_gateways: bool = Field(default=True, description="Collect NAT Gateways")
    collect_transit_gateways: bool = Field(default=True, description="Collect Transit Gateways")
    collect_security_groups: bool = Field(default=True, description="Collect Security Groups")
    collect_route_tables: bool = Field(default=True, description="Collect Route Tables")
    collect_network_acls: bool = Field(default=True, description="Collect Network ACLs")
    collect_vpc_peering: bool = Field(default=True, description="Collect VPC Peering connections")
    collect_vpn_connections: bool = Field(default=True, description="Collect VPN connections")
    collect_direct_connect: bool = Field(default=True, description="Collect Direct Connect connections")
    collect_load_balancers: bool = Field(default=True, description="Collect Load Balancers")
    collect_rds_instances: bool = Field(default=True, description="Collect RDS instances")
    collect_lambda_enis: bool = Field(default=True, description="Collect Lambda ENIs")

    # Security settings
    secrets_manager_enabled: bool = Field(
        default=False,
        description="Use AWS Secrets Manager for sensitive data"
    )
    encryption_at_rest: bool = Field(default=True, description="Enable encryption at rest")

    model_config = SettingsConfigDict(
        env_prefix="AWS_NET_VIZ_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment is one of the allowed values."""
        allowed = ["development", "staging", "production"]
        if v.lower() not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v.lower()

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return v.upper()

    @field_validator("default_output_format")
    @classmethod
    def validate_output_format(cls, v: str) -> str:
        """Validate output format is supported."""
        allowed = ["png", "svg", "html", "json"]
        if v.lower() not in allowed:
            raise ValueError(f"Output format must be one of {allowed}")
        return v.lower()

    def get_bedrock_region(self) -> str:
        """Get Bedrock region, defaulting to aws_region if not set."""
        return self.bedrock_region or self.aws_region

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    This function is cached to ensure we only create one settings instance
    per application lifecycle.

    Returns:
        Settings instance
    """
    return Settings()
