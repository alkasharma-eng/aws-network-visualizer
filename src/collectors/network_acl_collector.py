"""
Network ACL collector.

Collects Network ACL resources with comprehensive rule analysis
for enterprise security compliance and auditing.
"""

from typing import Any, Dict, List, Optional

from src.collectors.base import BaseCollector
from src.core.constants import ResourceType
from src.core.logging import get_logger

logger = get_logger(__name__)


class NetworkACLCollector(BaseCollector):
    """
    Collector for AWS Network ACL resources.

    Network ACLs are stateless firewalls that control inbound and outbound
    traffic at the subnet level.
    """

    def __init__(
        self,
        region: str,
        profile: Optional[str] = None,
        rate_limit: Optional[float] = None,
        vpc_id: Optional[str] = None,
    ):
        """
        Initialize Network ACL collector.

        Args:
            region: AWS region
            profile: AWS profile
            rate_limit: Rate limit in requests/second
            vpc_id: Optional VPC ID to filter network ACLs
        """
        super().__init__(region, profile, rate_limit)
        self.vpc_id = vpc_id

    @property
    def resource_type(self) -> ResourceType:
        """Resource type for this collector."""
        return ResourceType.NETWORK_ACL

    @property
    def service_name(self) -> str:
        """AWS service name."""
        return "ec2"

    async def collect_resources(self) -> List[Dict[str, Any]]:
        """
        Collect Network ACL resources.

        Returns:
            List of Network ACL dictionaries with normalized structure

        Raises:
            CollectorException: If collection fails
        """
        client = self.get_client()

        # Build filters
        filters = []
        if self.vpc_id:
            filters.append({"Name": "vpc-id", "Values": [self.vpc_id]})

        # Collect network ACLs with pagination
        kwargs = {}
        if filters:
            kwargs["Filters"] = filters

        network_acls = await self._paginated_call(
            client=client,
            method_name="describe_network_acls",
            result_key="NetworkAcls",
            **kwargs,
        )

        # Normalize network ACL data
        normalized_acls = []
        for acl in network_acls:
            entries = acl.get("Entries", [])
            associations = acl.get("Associations", [])

            # Parse ACL entries for security analysis
            parsed_entries = []
            ingress_rules = []
            egress_rules = []

            for entry in entries:
                is_egress = entry.get("Egress", False)
                rule_action = entry.get("RuleAction")

                parsed_entry = {
                    "rule_number": entry.get("RuleNumber"),
                    "protocol": self._parse_protocol(entry.get("Protocol")),
                    "rule_action": rule_action,  # allow or deny
                    "egress": is_egress,
                    "cidr_block": entry.get("CidrBlock"),
                    "ipv6_cidr_block": entry.get("Ipv6CidrBlock"),
                    "icmp_type_code": entry.get("IcmpTypeCode"),
                    "port_range": entry.get("PortRange"),
                }
                parsed_entries.append(parsed_entry)

                # Categorize rules for analysis
                if is_egress:
                    egress_rules.append(parsed_entry)
                else:
                    ingress_rules.append(parsed_entry)

            # Parse associations
            is_default = acl.get("IsDefault", False)
            associated_subnet_ids = [assoc.get("SubnetId") for assoc in associations]

            normalized_acl = {
                "id": acl["NetworkAclId"],
                "vpc_id": acl.get("VpcId"),
                "owner_id": acl.get("OwnerId"),
                "is_default": is_default,
                "entries": parsed_entries,
                "ingress_rules": ingress_rules,
                "egress_rules": egress_rules,
                "associations": [
                    {
                        "association_id": assoc.get("NetworkAclAssociationId"),
                        "subnet_id": assoc.get("SubnetId"),
                    }
                    for assoc in associations
                ],
                "associated_subnet_ids": associated_subnet_ids,
                "tags": self._extract_tags(acl.get("Tags", [])),
                "name": self._get_name_from_tags(acl.get("Tags", [])),
                "region": self.region,
                "resource_type": self.resource_type.value,
                # Enhanced metadata for enterprise security analysis
                "total_rules": len(entries),
                "ingress_rule_count": len(ingress_rules),
                "egress_rule_count": len(egress_rules),
                "allow_rules": len([e for e in entries if e.get("RuleAction") == "allow"]),
                "deny_rules": len([e for e in entries if e.get("RuleAction") == "deny"]),
                "subnet_count": len(associated_subnet_ids),
                "has_wide_open_ingress": self._check_wide_open_access(ingress_rules),
                "has_wide_open_egress": self._check_wide_open_access(egress_rules),
                "raw": acl,
            }
            normalized_acls.append(normalized_acl)

        logger.info(
            f"Collected {len(normalized_acls)} Network ACLs in {self.region}",
            extra={
                "count": len(normalized_acls),
                "region": self.region,
                "vpc_filter": self.vpc_id,
            },
        )

        return normalized_acls

    def _parse_protocol(self, protocol: str) -> str:
        """
        Parse protocol number to name.

        Args:
            protocol: Protocol number as string

        Returns:
            Protocol name
        """
        protocol_map = {
            "-1": "all",
            "1": "icmp",
            "6": "tcp",
            "17": "udp",
            "58": "icmpv6",
        }
        return protocol_map.get(protocol, protocol)

    def _check_wide_open_access(self, rules: List[Dict[str, Any]]) -> bool:
        """
        Check if rules allow unrestricted access (0.0.0.0/0).

        Args:
            rules: List of ACL rules

        Returns:
            True if wide-open access exists
        """
        for rule in rules:
            if rule.get("rule_action") == "allow":
                cidr = rule.get("cidr_block", "")
                if cidr == "0.0.0.0/0" or cidr == "::/0":
                    return True
        return False

    def _extract_tags(self, tags: List[Dict[str, str]]) -> Dict[str, str]:
        """Extract tags into a dictionary."""
        if not tags:
            return {}
        return {tag["Key"]: tag["Value"] for tag in tags}

    def _get_name_from_tags(self, tags: List[Dict[str, str]]) -> str:
        """Get the Name tag value."""
        if not tags:
            return ""
        for tag in tags:
            if tag.get("Key") == "Name":
                return tag.get("Value", "")
        return ""
