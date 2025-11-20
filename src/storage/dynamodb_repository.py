"""
DynamoDB repository for storing network topology data.

This module provides high-performance storage and retrieval of
network topology data using Amazon DynamoDB.
"""

import time
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from src.core.config import get_settings
from src.core.exceptions import StorageException
from src.core.logging import get_logger
from src.observability.metrics import get_metrics_publisher

logger = get_logger(__name__)


class DynamoDBRepository:
    """
    Repository for storing and retrieving topology data in DynamoDB.

    Schema:
        PK: region#vpc_id
        SK: timestamp
        Attributes: topology_data, metadata, ttl
    """

    def __init__(self, table_name: Optional[str] = None):
        """
        Initialize DynamoDB repository.

        Args:
            table_name: DynamoDB table name (defaults to config)
        """
        self.settings = get_settings()
        self.table_name = table_name or self.settings.dynamodb_table_name
        self.metrics = get_metrics_publisher()

        try:
            session = boto3.Session(
                profile_name=self.settings.aws_profile,
                region_name=self.settings.aws_region,
            )
            dynamodb = session.resource("dynamodb")
            self.table = dynamodb.Table(self.table_name)
            logger.info(f"Initialized DynamoDB repository: {self.table_name}")
        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB repository: {e}")
            raise StorageException(
                f"Failed to initialize DynamoDB: {e}",
                storage_type="dynamodb",
            )

    def save_topology(
        self,
        region: str,
        vpc_id: str,
        topology_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        ttl_days: int = 30,
    ) -> None:
        """
        Save network topology to DynamoDB.

        Args:
            region: AWS region
            vpc_id: VPC identifier
            topology_data: Topology data to store
            metadata: Additional metadata
            ttl_days: Time to live in days

        Raises:
            StorageException: If save fails
        """
        start_time = time.time()

        try:
            timestamp = int(time.time())
            ttl = timestamp + (ttl_days * 24 * 60 * 60)

            item = {
                "PK": f"{region}#{vpc_id}",
                "SK": timestamp,
                "region": region,
                "vpc_id": vpc_id,
                "topology_data": topology_data,
                "metadata": metadata or {},
                "ttl": ttl,
                "created_at": timestamp,
            }

            self.table.put_item(Item=item)

            duration = time.time() - start_time
            self.metrics.put_duration(
                "DynamoDBWriteLatency",
                duration,
                {"Operation": "save_topology"},
            )

            logger.info(
                f"Saved topology for {region}/{vpc_id}",
                extra={
                    "region": region,
                    "vpc_id": vpc_id,
                    "duration": duration,
                },
            )

        except ClientError as e:
            duration = time.time() - start_time
            logger.error(
                f"Failed to save topology: {e}",
                extra={"region": region, "vpc_id": vpc_id},
            )
            raise StorageException(
                f"Failed to save topology: {e}",
                operation="write",
                storage_type="dynamodb",
            )

    def get_latest_topology(
        self,
        region: str,
        vpc_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get the latest topology for a VPC.

        Args:
            region: AWS region
            vpc_id: VPC identifier

        Returns:
            Topology data or None if not found

        Raises:
            StorageException: If retrieval fails
        """
        start_time = time.time()

        try:
            response = self.table.query(
                KeyConditionExpression="PK = :pk",
                ExpressionAttributeValues={":pk": f"{region}#{vpc_id}"},
                ScanIndexForward=False,  # Sort descending (latest first)
                Limit=1,
            )

            duration = time.time() - start_time
            self.metrics.put_duration(
                "DynamoDBReadLatency",
                duration,
                {"Operation": "get_latest_topology"},
            )

            items = response.get("Items", [])
            if items:
                logger.info(
                    f"Retrieved topology for {region}/{vpc_id}",
                    extra={"region": region, "vpc_id": vpc_id},
                )
                return items[0]

            logger.debug(
                f"No topology found for {region}/{vpc_id}",
                extra={"region": region, "vpc_id": vpc_id},
            )
            return None

        except ClientError as e:
            logger.error(
                f"Failed to retrieve topology: {e}",
                extra={"region": region, "vpc_id": vpc_id},
            )
            raise StorageException(
                f"Failed to retrieve topology: {e}",
                operation="read",
                storage_type="dynamodb",
            )

    def get_topology_history(
        self,
        region: str,
        vpc_id: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get topology history for a VPC.

        Args:
            region: AWS region
            vpc_id: VPC identifier
            limit: Maximum number of records to return

        Returns:
            List of topology records

        Raises:
            StorageException: If retrieval fails
        """
        try:
            response = self.table.query(
                KeyConditionExpression="PK = :pk",
                ExpressionAttributeValues={":pk": f"{region}#{vpc_id}"},
                ScanIndexForward=False,
                Limit=limit,
            )

            items = response.get("Items", [])
            logger.info(
                f"Retrieved {len(items)} topology records for {region}/{vpc_id}",
                extra={"region": region, "vpc_id": vpc_id, "count": len(items)},
            )
            return items

        except ClientError as e:
            logger.error(f"Failed to retrieve topology history: {e}")
            raise StorageException(
                f"Failed to retrieve topology history: {e}",
                operation="read",
                storage_type="dynamodb",
            )

    def delete_topology(
        self,
        region: str,
        vpc_id: str,
        timestamp: int,
    ) -> None:
        """
        Delete a specific topology record.

        Args:
            region: AWS region
            vpc_id: VPC identifier
            timestamp: Record timestamp

        Raises:
            StorageException: If deletion fails
        """
        try:
            self.table.delete_item(
                Key={"PK": f"{region}#{vpc_id}", "SK": timestamp}
            )

            logger.info(
                f"Deleted topology for {region}/{vpc_id} at {timestamp}",
                extra={"region": region, "vpc_id": vpc_id, "timestamp": timestamp},
            )

        except ClientError as e:
            logger.error(f"Failed to delete topology: {e}")
            raise StorageException(
                f"Failed to delete topology: {e}",
                operation="delete",
                storage_type="dynamodb",
            )

    def scan_all_topologies(
        self,
        region: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Scan all topology records, optionally filtered by region.

        Args:
            region: Optional region filter
            limit: Maximum number of records

        Returns:
            List of topology records

        Raises:
            StorageException: If scan fails
        """
        try:
            scan_kwargs = {}

            if region:
                scan_kwargs["FilterExpression"] = "region = :region"
                scan_kwargs["ExpressionAttributeValues"] = {":region": region}

            if limit:
                scan_kwargs["Limit"] = limit

            response = self.table.scan(**scan_kwargs)
            items = response.get("Items", [])

            # Handle pagination
            while "LastEvaluatedKey" in response and (
                not limit or len(items) < limit
            ):
                scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
                response = self.table.scan(**scan_kwargs)
                items.extend(response.get("Items", []))

            logger.info(f"Scanned {len(items)} topology records")
            return items

        except ClientError as e:
            logger.error(f"Failed to scan topologies: {e}")
            raise StorageException(
                f"Failed to scan topologies: {e}",
                operation="scan",
                storage_type="dynamodb",
            )
