"""
S3 repository for storing visualizations and archives.

This module provides storage for large files like visualizations,
topology archives, and analysis reports.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from src.core.config import get_settings
from src.core.exceptions import StorageException
from src.core.logging import get_logger
from src.observability.metrics import get_metrics_publisher

logger = get_logger(__name__)


class S3Repository:
    """
    Repository for storing files in Amazon S3.

    Bucket structure:
        /topologies/{region}/{vpc_id}/{timestamp}.json
        /visualizations/{region}/{vpc_id}/{timestamp}.png
        /analyses/{region}/{vpc_id}/{timestamp}.json
        /archives/{date}/{full_topology}.json.gz
    """

    def __init__(self, bucket_name: Optional[str] = None):
        """
        Initialize S3 repository.

        Args:
            bucket_name: S3 bucket name (defaults to config)
        """
        self.settings = get_settings()
        self.bucket_name = bucket_name or self.settings.s3_bucket_name
        self.metrics = get_metrics_publisher()

        if not self.bucket_name:
            logger.warning("S3 bucket name not configured, S3 storage disabled")
            self.client = None
            return

        try:
            session = boto3.Session(
                profile_name=self.settings.aws_profile,
                region_name=self.settings.aws_region,
            )
            self.client = session.client("s3")
            logger.info(f"Initialized S3 repository: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Failed to initialize S3 repository: {e}")
            raise StorageException(
                f"Failed to initialize S3: {e}",
                storage_type="s3",
            )

    def upload_topology(
        self,
        region: str,
        vpc_id: str,
        topology_data: Dict[str, Any],
        timestamp: Optional[int] = None,
    ) -> str:
        """
        Upload topology data to S3.

        Args:
            region: AWS region
            vpc_id: VPC identifier
            topology_data: Topology data
            timestamp: Optional timestamp (defaults to now)

        Returns:
            S3 object key

        Raises:
            StorageException: If upload fails
        """
        if not self.client:
            raise StorageException(
                "S3 client not initialized",
                storage_type="s3",
            )

        start_time = time.time()
        timestamp = timestamp or int(time.time())
        key = f"topologies/{region}/{vpc_id}/{timestamp}.json"

        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json.dumps(topology_data, indent=2, default=str),
                ContentType="application/json",
                ServerSideEncryption="AES256",
            )

            duration = time.time() - start_time
            self.metrics.put_duration(
                "S3UploadDuration",
                duration,
                {"Operation": "upload_topology"},
            )

            logger.info(
                f"Uploaded topology to s3://{self.bucket_name}/{key}",
                extra={"key": key, "duration": duration},
            )

            return key

        except ClientError as e:
            logger.error(f"Failed to upload topology: {e}")
            raise StorageException(
                f"Failed to upload topology: {e}",
                operation="write",
                storage_type="s3",
            )

    def download_topology(
        self,
        key: str,
    ) -> Dict[str, Any]:
        """
        Download topology data from S3.

        Args:
            key: S3 object key

        Returns:
            Topology data

        Raises:
            StorageException: If download fails
        """
        if not self.client:
            raise StorageException(
                "S3 client not initialized",
                storage_type="s3",
            )

        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=key)
            data = json.loads(response["Body"].read())

            logger.info(
                f"Downloaded topology from s3://{self.bucket_name}/{key}",
                extra={"key": key},
            )

            return data

        except ClientError as e:
            logger.error(f"Failed to download topology: {e}")
            raise StorageException(
                f"Failed to download topology: {e}",
                operation="read",
                storage_type="s3",
            )

    def upload_visualization(
        self,
        region: str,
        vpc_id: str,
        image_data: bytes,
        format: str = "png",
        timestamp: Optional[int] = None,
    ) -> str:
        """
        Upload visualization image to S3.

        Args:
            region: AWS region
            vpc_id: VPC identifier
            image_data: Image bytes
            format: Image format (png, svg, etc.)
            timestamp: Optional timestamp

        Returns:
            S3 object key

        Raises:
            StorageException: If upload fails
        """
        if not self.client:
            raise StorageException(
                "S3 client not initialized",
                storage_type="s3",
            )

        timestamp = timestamp or int(time.time())
        key = f"visualizations/{region}/{vpc_id}/{timestamp}.{format}"

        content_types = {
            "png": "image/png",
            "svg": "image/svg+xml",
            "html": "text/html",
        }

        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=image_data,
                ContentType=content_types.get(format, "application/octet-stream"),
                ServerSideEncryption="AES256",
            )

            logger.info(
                f"Uploaded visualization to s3://{self.bucket_name}/{key}",
                extra={"key": key, "format": format},
            )

            return key

        except ClientError as e:
            logger.error(f"Failed to upload visualization: {e}")
            raise StorageException(
                f"Failed to upload visualization: {e}",
                operation="write",
                storage_type="s3",
            )

    def list_topologies(
        self,
        region: Optional[str] = None,
        vpc_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List topology files in S3.

        Args:
            region: Optional region filter
            vpc_id: Optional VPC filter

        Returns:
            List of S3 object metadata

        Raises:
            StorageException: If listing fails
        """
        if not self.client:
            raise StorageException(
                "S3 client not initialized",
                storage_type="s3",
            )

        prefix = "topologies/"
        if region:
            prefix += f"{region}/"
            if vpc_id:
                prefix += f"{vpc_id}/"

        try:
            paginator = self.client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)

            objects = []
            for page in pages:
                for obj in page.get("Contents", []):
                    objects.append(
                        {
                            "key": obj["Key"],
                            "size": obj["Size"],
                            "last_modified": obj["LastModified"],
                        }
                    )

            logger.info(
                f"Listed {len(objects)} topology files",
                extra={"prefix": prefix, "count": len(objects)},
            )

            return objects

        except ClientError as e:
            logger.error(f"Failed to list topologies: {e}")
            raise StorageException(
                f"Failed to list topologies: {e}",
                operation="list",
                storage_type="s3",
            )

    def delete_object(self, key: str) -> None:
        """
        Delete an object from S3.

        Args:
            key: S3 object key

        Raises:
            StorageException: If deletion fails
        """
        if not self.client:
            raise StorageException(
                "S3 client not initialized",
                storage_type="s3",
            )

        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)

            logger.info(
                f"Deleted s3://{self.bucket_name}/{key}",
                extra={"key": key},
            )

        except ClientError as e:
            logger.error(f"Failed to delete object: {e}")
            raise StorageException(
                f"Failed to delete object: {e}",
                operation="delete",
                storage_type="s3",
            )

    def generate_presigned_url(
        self,
        key: str,
        expiration: int = 3600,
    ) -> str:
        """
        Generate a presigned URL for downloading an object.

        Args:
            key: S3 object key
            expiration: URL expiration time in seconds

        Returns:
            Presigned URL

        Raises:
            StorageException: If URL generation fails
        """
        if not self.client:
            raise StorageException(
                "S3 client not initialized",
                storage_type="s3",
            )

        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expiration,
            )

            logger.info(
                f"Generated presigned URL for {key}",
                extra={"key": key, "expiration": expiration},
            )

            return url

        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise StorageException(
                f"Failed to generate presigned URL: {e}",
                operation="presign",
                storage_type="s3",
            )
