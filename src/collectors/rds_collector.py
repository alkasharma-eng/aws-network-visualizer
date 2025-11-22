"""
RDS Instance collector.

Collects RDS database instances and clusters for enterprise
database network topology visualization and analysis.
"""

from typing import Any, Dict, List, Optional

from src.collectors.base import BaseCollector
from src.core.constants import ResourceType
from src.core.logging import get_logger

logger = get_logger(__name__)


class RDSCollector(BaseCollector):
    """
    Collector for AWS RDS (Relational Database Service) resources.

    Collects RDS instances, Aurora clusters, and their network configurations
    including VPC placement, subnets, and security groups.
    """

    def __init__(
        self,
        region: str,
        profile: Optional[str] = None,
        rate_limit: Optional[float] = None,
        vpc_id: Optional[str] = None,
    ):
        """
        Initialize RDS collector.

        Args:
            region: AWS region
            profile: AWS profile
            rate_limit: Rate limit in requests/second
            vpc_id: Optional VPC ID to filter RDS instances
        """
        super().__init__(region, profile, rate_limit)
        self.vpc_id = vpc_id

    @property
    def resource_type(self) -> ResourceType:
        """Resource type for this collector."""
        return ResourceType.RDS_INSTANCE

    @property
    def service_name(self) -> str:
        """AWS service name."""
        return "rds"

    async def collect_resources(self) -> List[Dict[str, Any]]:
        """
        Collect RDS resources.

        Returns:
            List of RDS dictionaries with normalized structure

        Raises:
            CollectorException: If collection fails
        """
        all_resources = []

        # Collect RDS instances
        instances = await self._collect_db_instances()
        all_resources.extend(instances)

        # Collect RDS clusters (Aurora, etc.)
        clusters = await self._collect_db_clusters()
        all_resources.extend(clusters)

        logger.info(
            f"Collected {len(all_resources)} RDS resources ({len(instances)} instances, {len(clusters)} clusters) in {self.region}",
            extra={
                "total_count": len(all_resources),
                "instance_count": len(instances),
                "cluster_count": len(clusters),
                "region": self.region,
            },
        )

        return all_resources

    async def _collect_db_instances(self) -> List[Dict[str, Any]]:
        """
        Collect RDS DB instances.

        Returns:
            List of normalized DB instance dictionaries
        """
        client = self.get_client()

        # Collect DB instances with pagination
        db_instances = await self._paginated_call(
            client=client,
            method_name="describe_db_instances",
            result_key="DBInstances",
        )

        # Filter by VPC if specified
        if self.vpc_id:
            db_instances = [
                db for db in db_instances if db.get("DBSubnetGroup", {}).get("VpcId") == self.vpc_id
            ]

        # Normalize DB instance data
        normalized_instances = []
        for db in db_instances:
            subnet_group = db.get("DBSubnetGroup", {})
            endpoint = db.get("Endpoint", {})
            vpc_security_groups = db.get("VpcSecurityGroups", [])

            normalized_db = {
                "id": db.get("DBInstanceIdentifier"),
                "arn": db.get("DBInstanceArn"),
                "resource_type_detail": "db_instance",
                "db_instance_class": db.get("DBInstanceClass"),
                "engine": db.get("Engine"),
                "engine_version": db.get("EngineVersion"),
                "db_instance_status": db.get("DBInstanceStatus"),
                "master_username": db.get("MasterUsername"),
                "db_name": db.get("DBName"),
                # Network configuration
                "endpoint_address": endpoint.get("Address"),
                "endpoint_port": endpoint.get("Port"),
                "endpoint_hosted_zone_id": endpoint.get("HostedZoneId"),
                "publicly_accessible": db.get("PubliclyAccessible"),
                "vpc_id": subnet_group.get("VpcId"),
                "db_subnet_group_name": subnet_group.get("DBSubnetGroupName"),
                "db_subnet_group_description": subnet_group.get("DBSubnetGroupDescription"),
                "subnet_ids": [subnet.get("SubnetIdentifier") for subnet in subnet_group.get("Subnets", [])],
                "availability_zone": db.get("AvailabilityZone"),
                "secondary_availability_zone": db.get("SecondaryAvailabilityZone"),
                "multi_az": db.get("MultiAZ"),
                # Security
                "vpc_security_groups": [
                    {
                        "security_group_id": sg.get("VpcSecurityGroupId"),
                        "status": sg.get("Status"),
                    }
                    for sg in vpc_security_groups
                ],
                "security_group_ids": [sg.get("VpcSecurityGroupId") for sg in vpc_security_groups],
                "iam_database_authentication_enabled": db.get("IAMDatabaseAuthenticationEnabled"),
                "deletion_protection": db.get("DeletionProtection"),
                # Storage
                "allocated_storage": db.get("AllocatedStorage"),
                "storage_type": db.get("StorageType"),
                "storage_encrypted": db.get("StorageEncrypted"),
                "kms_key_id": db.get("KmsKeyId"),
                # Backup and maintenance
                "backup_retention_period": db.get("BackupRetentionPeriod"),
                "preferred_backup_window": db.get("PreferredBackupWindow"),
                "preferred_maintenance_window": db.get("PreferredMaintenanceWindow"),
                "latest_restorable_time": (
                    db.get("LatestRestorableTime").isoformat() if db.get("LatestRestorableTime") else None
                ),
                "auto_minor_version_upgrade": db.get("AutoMinorVersionUpgrade"),
                # Performance and monitoring
                "performance_insights_enabled": db.get("PerformanceInsightsEnabled"),
                "performance_insights_kms_key_id": db.get("PerformanceInsightsKMSKeyId"),
                "monitoring_interval": db.get("MonitoringInterval"),
                "monitoring_role_arn": db.get("MonitoringRoleArn"),
                "enhanced_monitoring_resource_arn": db.get("EnhancedMonitoringResourceArn"),
                # Cluster information (for Aurora replicas)
                "db_cluster_identifier": db.get("DBClusterIdentifier"),
                "read_replica_source_db_instance_identifier": db.get("ReadReplicaSourceDBInstanceIdentifier"),
                "read_replica_db_instance_identifiers": db.get("ReadReplicaDBInstanceIdentifiers", []),
                # Timestamps
                "instance_create_time": (
                    db.get("InstanceCreateTime").isoformat() if db.get("InstanceCreateTime") else None
                ),
                # Tags
                "tags": self._extract_rds_tags(db.get("TagList", [])),
                "name": self._get_name_from_rds_tags(db.get("TagList", [])),
                "region": self.region,
                "resource_type": self.resource_type.value,
                # Enhanced metadata for enterprise analysis
                "is_multi_az": db.get("MultiAZ", False),
                "is_encrypted": db.get("StorageEncrypted", False),
                "is_publicly_accessible": db.get("PubliclyAccessible", False),
                "is_production_ready": (
                    db.get("MultiAZ", False)
                    and db.get("DeletionProtection", False)
                    and db.get("BackupRetentionPeriod", 0) > 0
                ),
                "subnet_count": len(subnet_group.get("Subnets", [])),
                "security_group_count": len(vpc_security_groups),
                "is_read_replica": db.get("ReadReplicaSourceDBInstanceIdentifier") is not None,
                "replica_count": len(db.get("ReadReplicaDBInstanceIdentifiers", [])),
                "raw": db,
            }
            normalized_instances.append(normalized_db)

        return normalized_instances

    async def _collect_db_clusters(self) -> List[Dict[str, Any]]:
        """
        Collect RDS DB clusters (Aurora).

        Returns:
            List of normalized DB cluster dictionaries
        """
        client = self.get_client()

        # Collect DB clusters with pagination
        try:
            db_clusters = await self._paginated_call(
                client=client,
                method_name="describe_db_clusters",
                result_key="DBClusters",
            )
        except Exception as e:
            logger.warning(f"Could not collect DB clusters: {e}")
            return []

        # Filter by VPC if specified
        if self.vpc_id:
            db_clusters = [cluster for cluster in db_clusters if cluster.get("VpcId") == self.vpc_id]

        # Normalize DB cluster data
        normalized_clusters = []
        for cluster in db_clusters:
            vpc_security_groups = cluster.get("VpcSecurityGroups", [])

            normalized_cluster = {
                "id": cluster.get("DBClusterIdentifier"),
                "arn": cluster.get("DBClusterArn"),
                "resource_type_detail": "db_cluster",
                "engine": cluster.get("Engine"),
                "engine_version": cluster.get("EngineVersion"),
                "engine_mode": cluster.get("EngineMode"),  # provisioned, serverless, parallelquery, global
                "status": cluster.get("Status"),
                "master_username": cluster.get("MasterUsername"),
                "database_name": cluster.get("DatabaseName"),
                # Network configuration
                "endpoint": cluster.get("Endpoint"),
                "reader_endpoint": cluster.get("ReaderEndpoint"),
                "port": cluster.get("Port"),
                "hosted_zone_id": cluster.get("HostedZoneId"),
                "vpc_id": cluster.get("VpcId"),
                "db_subnet_group": cluster.get("DBSubnetGroup"),
                "availability_zones": cluster.get("AvailabilityZones", []),
                # Cluster members
                "db_cluster_members": [
                    {
                        "db_instance_identifier": member.get("DBInstanceIdentifier"),
                        "is_cluster_writer": member.get("IsClusterWriter"),
                        "db_cluster_parameter_group_status": member.get("DBClusterParameterGroupStatus"),
                        "promotion_tier": member.get("PromotionTier"),
                    }
                    for member in cluster.get("DBClusterMembers", [])
                ],
                "member_instance_ids": [
                    member.get("DBInstanceIdentifier") for member in cluster.get("DBClusterMembers", [])
                ],
                # Security
                "vpc_security_groups": [
                    {
                        "security_group_id": sg.get("VpcSecurityGroupId"),
                        "status": sg.get("Status"),
                    }
                    for sg in vpc_security_groups
                ],
                "security_group_ids": [sg.get("VpcSecurityGroupId") for sg in vpc_security_groups],
                "iam_database_authentication_enabled": cluster.get("IAMDatabaseAuthenticationEnabled"),
                "deletion_protection": cluster.get("DeletionProtection"),
                # Storage
                "storage_encrypted": cluster.get("StorageEncrypted"),
                "kms_key_id": cluster.get("KmsKeyId"),
                "allocated_storage": cluster.get("AllocatedStorage"),
                # Backup
                "backup_retention_period": cluster.get("BackupRetentionPeriod"),
                "preferred_backup_window": cluster.get("PreferredBackupWindow"),
                "preferred_maintenance_window": cluster.get("PreferredMaintenanceWindow"),
                # Timestamps
                "cluster_create_time": (
                    cluster.get("ClusterCreateTime").isoformat() if cluster.get("ClusterCreateTime") else None
                ),
                "earliest_restorable_time": (
                    cluster.get("EarliestRestorableTime").isoformat()
                    if cluster.get("EarliestRestorableTime")
                    else None
                ),
                "latest_restorable_time": (
                    cluster.get("LatestRestorableTime").isoformat()
                    if cluster.get("LatestRestorableTime")
                    else None
                ),
                # Global database
                "global_write_forwarding_status": cluster.get("GlobalWriteForwardingStatus"),
                "global_write_forwarding_requested": cluster.get("GlobalWriteForwardingRequested"),
                # Tags
                "tags": self._extract_rds_tags(cluster.get("TagList", [])),
                "name": self._get_name_from_rds_tags(cluster.get("TagList", [])),
                "region": self.region,
                "resource_type": self.resource_type.value,
                # Enhanced metadata
                "is_encrypted": cluster.get("StorageEncrypted", False),
                "is_multi_az": len(cluster.get("AvailabilityZones", [])) > 1,
                "member_count": len(cluster.get("DBClusterMembers", [])),
                "security_group_count": len(vpc_security_groups),
                "availability_zone_count": len(cluster.get("AvailabilityZones", [])),
                "is_serverless": cluster.get("EngineMode") == "serverless",
                "is_global": cluster.get("GlobalWriteForwardingStatus") is not None,
                "raw": cluster,
            }
            normalized_clusters.append(normalized_cluster)

        return normalized_clusters

    def _extract_rds_tags(self, tags: List[Dict[str, str]]) -> Dict[str, str]:
        """Extract RDS tags into a dictionary."""
        if not tags:
            return {}
        return {tag.get("Key", ""): tag.get("Value", "") for tag in tags}

    def _get_name_from_rds_tags(self, tags: List[Dict[str, str]]) -> str:
        """Get the Name tag value from RDS tags."""
        if not tags:
            return ""
        for tag in tags:
            if tag.get("Key") == "Name":
                return tag.get("Value", "")
        return ""
