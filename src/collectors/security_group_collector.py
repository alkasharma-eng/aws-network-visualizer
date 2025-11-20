"""
Security Group collector.
"""

from typing import Any, Dict, List, Optional

from src.collectors.base import BaseCollector
from src.core.constants import ResourceType
from src.core.logging import get_logger

logger = get_logger(__name__)


class SecurityGroupCollector(BaseCollector):
    """
    Collector for AWS Security Group resources.
    """

    def __init__(
        self,
        region: str,
        profile: Optional[str] = None,
        rate_limit: Optional[float] = None,
        vpc_id: Optional[str] = None,
    ):
        """
        Initialize Security Group collector.

        Args:
            region: AWS region
            profile: AWS profile
            rate_limit: Rate limit in requests/second
            vpc_id: Optional VPC ID to filter security groups
        """
        super().__init__(region, profile, rate_limit)
        self.vpc_id = vpc_id

    @property
    def resource_type(self) -> ResourceType:
        """Resource type for this collector."""
        return ResourceType.SECURITY_GROUP

    @property
    def service_name(self) -> str:
        """AWS service name."""
        return "ec2"

    async def collect_resources(self) -> List[Dict[str, Any]]:
        """
        Collect Security Group resources.

        Returns:
            List of Security Group dictionaries with normalized structure

        Raises:
            CollectorException: If collection fails
        """
        client = self.get_client()

        # Build filters
        filters = []
        if self.vpc_id:
            filters.append({"Name": "vpc-id", "Values": [self.vpc_id]})

        # Collect security groups with pagination
        kwargs = {}
        if filters:
            kwargs["Filters"] = filters

        security_groups = await self._paginated_call(
            client=client,
            method_name="describe_security_groups",
            result_key="SecurityGroups",
            **kwargs,
        )

        # Normalize security group data
        normalized_sgs = []
        for sg in security_groups:
            normalized_sg = {
                "id": sg["GroupId"],
                "name": sg.get("GroupName"),
                "description": sg.get("Description"),
                "vpc_id": sg.get("VpcId"),
                "ingress_rules": self._normalize_rules(sg.get("IpPermissions", [])),
                "egress_rules": self._normalize_rules(
                    sg.get("IpPermissionsEgress", [])
                ),
                "tags": self._extract_tags(sg.get("Tags", [])),
                "region": self.region,
                "resource_type": self.resource_type.value,
                "raw": sg,
            }
            normalized_sgs.append(normalized_sg)

        return normalized_sgs

    def _normalize_rules(self, rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize security group rules.

        Args:
            rules: List of rule dictionaries

        Returns:
            List of normalized rules
        """
        normalized_rules = []

        for rule in rules:
            normalized_rule = {
                "ip_protocol": rule.get("IpProtocol"),
                "from_port": rule.get("FromPort"),
                "to_port": rule.get("ToPort"),
                "ip_ranges": [
                    {
                        "cidr": ip_range.get("CidrIp"),
                        "description": ip_range.get("Description"),
                    }
                    for ip_range in rule.get("IpRanges", [])
                ],
                "ipv6_ranges": [
                    {
                        "cidr": ip_range.get("CidrIpv6"),
                        "description": ip_range.get("Description"),
                    }
                    for ip_range in rule.get("Ipv6Ranges", [])
                ],
                "prefix_list_ids": [
                    pl.get("PrefixListId") for pl in rule.get("PrefixListIds", [])
                ],
                "user_id_group_pairs": [
                    {
                        "group_id": pair.get("GroupId"),
                        "vpc_id": pair.get("VpcId"),
                        "description": pair.get("Description"),
                    }
                    for pair in rule.get("UserIdGroupPairs", [])
                ],
            }
            normalized_rules.append(normalized_rule)

        return normalized_rules

    def _extract_tags(self, tags: List[Dict[str, str]]) -> Dict[str, str]:
        """Extract tags into a dictionary."""
        if not tags:
            return {}
        return {tag["Key"]: tag["Value"] for tag in tags}
