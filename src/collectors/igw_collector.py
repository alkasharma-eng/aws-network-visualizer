"""
Internet Gateway collector.
"""

from typing import Any, Dict, List, Optional

from src.collectors.base import BaseCollector
from src.core.constants import ResourceType
from src.core.logging import get_logger

logger = get_logger(__name__)


class InternetGatewayCollector(BaseCollector):
    """
    Collector for AWS Internet Gateway resources.
    """

    def __init__(
        self,
        region: str,
        profile: Optional[str] = None,
        rate_limit: Optional[float] = None,
        vpc_id: Optional[str] = None,
    ):
        """
        Initialize Internet Gateway collector.

        Args:
            region: AWS region
            profile: AWS profile
            rate_limit: Rate limit in requests/second
            vpc_id: Optional VPC ID to filter internet gateways
        """
        super().__init__(region, profile, rate_limit)
        self.vpc_id = vpc_id

    @property
    def resource_type(self) -> ResourceType:
        """Resource type for this collector."""
        return ResourceType.INTERNET_GATEWAY

    @property
    def service_name(self) -> str:
        """AWS service name."""
        return "ec2"

    async def collect_resources(self) -> List[Dict[str, Any]]:
        """
        Collect Internet Gateway resources.

        Returns:
            List of Internet Gateway dictionaries with normalized structure

        Raises:
            CollectorException: If collection fails
        """
        client = self.get_client()

        # Build filters
        filters = []
        if self.vpc_id:
            filters.append({"Name": "attachment.vpc-id", "Values": [self.vpc_id]})

        # Collect internet gateways with pagination
        kwargs = {}
        if filters:
            kwargs["Filters"] = filters

        igws = await self._paginated_call(
            client=client,
            method_name="describe_internet_gateways",
            result_key="InternetGateways",
            **kwargs,
        )

        # Normalize internet gateway data
        normalized_igws = []
        for igw in igws:
            attachments = igw.get("Attachments", [])
            normalized_igw = {
                "id": igw["InternetGatewayId"],
                "attachments": [
                    {
                        "vpc_id": att.get("VpcId"),
                        "state": att.get("State"),
                    }
                    for att in attachments
                ],
                "attached_vpc_ids": [att.get("VpcId") for att in attachments],
                "tags": self._extract_tags(igw.get("Tags", [])),
                "name": self._get_name_from_tags(igw.get("Tags", [])),
                "region": self.region,
                "resource_type": self.resource_type.value,
                "raw": igw,
            }
            normalized_igws.append(normalized_igw)

        return normalized_igws

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
