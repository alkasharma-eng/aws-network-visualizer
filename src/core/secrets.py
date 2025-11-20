"""
AWS Secrets Manager Integration
Provides secure access to secrets with caching and automatic rotation support
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from functools import lru_cache

import boto3
from botocore.exceptions import ClientError

from src.core.config import get_settings
from src.core.exceptions import NetworkVisualizerException

logger = logging.getLogger(__name__)


class SecretsManagerException(NetworkVisualizerException):
    """Exception raised for Secrets Manager errors"""
    pass


class SecretsManager:
    """
    Manages access to AWS Secrets Manager with caching and error handling
    """

    def __init__(self, region: Optional[str] = None):
        """
        Initialize Secrets Manager client

        Args:
            region: AWS region (defaults to settings)
        """
        self.settings = get_settings()
        self.region = region or self.settings.aws_region
        self.client = boto3.client('secretsmanager', region_name=self.region)
        self._cache: Dict[str, tuple[Any, datetime]] = {}
        self._cache_ttl = timedelta(minutes=5)

    def get_secret(self, secret_name: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Retrieve secret from AWS Secrets Manager

        Args:
            secret_name: Name or ARN of the secret
            use_cache: Whether to use cached value

        Returns:
            Secret value as dictionary

        Raises:
            SecretsManagerException: If secret cannot be retrieved
        """
        # Check cache
        if use_cache and secret_name in self._cache:
            value, cached_time = self._cache[secret_name]
            if datetime.now() - cached_time < self._cache_ttl:
                logger.debug(f"Using cached value for secret: {secret_name}")
                return value

        try:
            logger.info(f"Retrieving secret from Secrets Manager: {secret_name}")
            response = self.client.get_secret_value(SecretId=secret_name)

            # Parse secret string
            if 'SecretString' in response:
                secret_value = json.loads(response['SecretString'])
            else:
                # Binary secret
                secret_value = response['SecretBinary']

            # Cache the value
            self._cache[secret_name] = (secret_value, datetime.now())

            logger.info(f"Successfully retrieved secret: {secret_name}")
            return secret_value

        except ClientError as e:
            error_code = e.response['Error']['Code']

            if error_code == 'ResourceNotFoundException':
                raise SecretsManagerException(f"Secret not found: {secret_name}")
            elif error_code == 'InvalidRequestException':
                raise SecretsManagerException(f"Invalid request for secret: {secret_name}")
            elif error_code == 'InvalidParameterException':
                raise SecretsManagerException(f"Invalid parameter for secret: {secret_name}")
            elif error_code == 'DecryptionFailure':
                raise SecretsManagerException(f"Failed to decrypt secret: {secret_name}")
            elif error_code == 'InternalServiceError':
                raise SecretsManagerException(f"Internal service error retrieving secret: {secret_name}")
            else:
                raise SecretsManagerException(f"Error retrieving secret {secret_name}: {str(e)}")

        except json.JSONDecodeError as e:
            raise SecretsManagerException(f"Failed to parse secret value for {secret_name}: {str(e)}")

        except Exception as e:
            raise SecretsManagerException(f"Unexpected error retrieving secret {secret_name}: {str(e)}")

    def get_secret_value(self, secret_name: str, key: str, use_cache: bool = True) -> Any:
        """
        Get specific value from a secret

        Args:
            secret_name: Name or ARN of the secret
            key: Key within the secret dictionary
            use_cache: Whether to use cached value

        Returns:
            Value for the specified key

        Raises:
            SecretsManagerException: If key not found or secret cannot be retrieved
        """
        secret = self.get_secret(secret_name, use_cache=use_cache)

        if key not in secret:
            raise SecretsManagerException(f"Key '{key}' not found in secret '{secret_name}'")

        return secret[key]

    def update_secret(self, secret_name: str, secret_value: Dict[str, Any]) -> None:
        """
        Update secret value in AWS Secrets Manager

        Args:
            secret_name: Name or ARN of the secret
            secret_value: New secret value as dictionary

        Raises:
            SecretsManagerException: If secret cannot be updated
        """
        try:
            logger.info(f"Updating secret: {secret_name}")

            self.client.update_secret(
                SecretId=secret_name,
                SecretString=json.dumps(secret_value)
            )

            # Invalidate cache
            if secret_name in self._cache:
                del self._cache[secret_name]

            logger.info(f"Successfully updated secret: {secret_name}")

        except ClientError as e:
            raise SecretsManagerException(f"Failed to update secret {secret_name}: {str(e)}")

    def create_secret(self, secret_name: str, secret_value: Dict[str, Any],
                     description: str = "") -> str:
        """
        Create new secret in AWS Secrets Manager

        Args:
            secret_name: Name for the new secret
            secret_value: Secret value as dictionary
            description: Description of the secret

        Returns:
            ARN of created secret

        Raises:
            SecretsManagerException: If secret cannot be created
        """
        try:
            logger.info(f"Creating new secret: {secret_name}")

            response = self.client.create_secret(
                Name=secret_name,
                Description=description,
                SecretString=json.dumps(secret_value)
            )

            arn = response['ARN']
            logger.info(f"Successfully created secret: {secret_name} (ARN: {arn})")
            return arn

        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceExistsException':
                raise SecretsManagerException(f"Secret already exists: {secret_name}")
            raise SecretsManagerException(f"Failed to create secret {secret_name}: {str(e)}")

    def delete_secret(self, secret_name: str, recovery_window_days: int = 30) -> None:
        """
        Delete secret from AWS Secrets Manager

        Args:
            secret_name: Name or ARN of the secret
            recovery_window_days: Days to retain deleted secret (7-30)

        Raises:
            SecretsManagerException: If secret cannot be deleted
        """
        try:
            logger.info(f"Deleting secret: {secret_name} (recovery window: {recovery_window_days} days)")

            self.client.delete_secret(
                SecretId=secret_name,
                RecoveryWindowInDays=recovery_window_days
            )

            # Remove from cache
            if secret_name in self._cache:
                del self._cache[secret_name]

            logger.info(f"Successfully scheduled deletion for secret: {secret_name}")

        except ClientError as e:
            raise SecretsManagerException(f"Failed to delete secret {secret_name}: {str(e)}")

    def clear_cache(self) -> None:
        """Clear all cached secrets"""
        self._cache.clear()
        logger.debug("Cleared secrets cache")


@lru_cache(maxsize=1)
def get_secrets_manager() -> SecretsManager:
    """
    Get singleton instance of SecretsManager

    Returns:
        SecretsManager instance
    """
    return SecretsManager()


# Convenience functions for common secrets
def get_api_keys() -> Dict[str, str]:
    """Get API keys from Secrets Manager"""
    settings = get_settings()
    secret_name = f"network-visualizer/api-keys-{settings.environment}"
    manager = get_secrets_manager()
    return manager.get_secret(secret_name)


def get_database_credentials() -> Dict[str, Any]:
    """Get database credentials from Secrets Manager"""
    settings = get_settings()
    secret_name = f"network-visualizer/database-{settings.environment}"
    manager = get_secrets_manager()
    return manager.get_secret(secret_name)


def get_integration_credentials() -> Dict[str, str]:
    """Get third-party integration credentials from Secrets Manager"""
    settings = get_settings()
    secret_name = f"network-visualizer/integrations-{settings.environment}"
    manager = get_secrets_manager()
    return manager.get_secret(secret_name)
