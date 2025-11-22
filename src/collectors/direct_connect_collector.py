"""
Direct Connect collector.

Collects AWS Direct Connect connections and virtual interfaces for
enterprise hybrid cloud network visualization.
"""

from typing import Any, Dict, List, Optional

from src.collectors.base import BaseCollector
from src.core.constants import ResourceType
from src.core.logging import get_logger

logger = get_logger(__name__)


class DirectConnectCollector(BaseCollector):
    """
    Collector for AWS Direct Connect resources.

    Direct Connect provides dedicated network connections from on-premises
    to AWS. Critical for enterprise workloads requiring high throughput,
    low latency, and consistent network performance.
    """

    def __init__(
        self,
        region: str,
        profile: Optional[str] = None,
        rate_limit: Optional[float] = None,
    ):
        """
        Initialize Direct Connect collector.

        Args:
            region: AWS region
            profile: AWS profile
            rate_limit: Rate limit in requests/second
        """
        super().__init__(region, profile, rate_limit)

    @property
    def resource_type(self) -> ResourceType:
        """Resource type for this collector."""
        return ResourceType.DIRECT_CONNECT

    @property
    def service_name(self) -> str:
        """AWS service name."""
        return "directconnect"

    async def collect_resources(self) -> List[Dict[str, Any]]:
        """
        Collect Direct Connect resources.

        Returns:
            List of Direct Connect dictionaries with normalized structure

        Raises:
            CollectorException: If collection fails
        """
        client = self.get_client()

        # Collect Direct Connect connections
        dx_response = await self._simple_call(
            client=client,
            method_name="describe_connections",
        )
        connections = dx_response.get("connections", [])

        # Collect Virtual Interfaces
        vif_response = await self._simple_call(
            client=client,
            method_name="describe_virtual_interfaces",
        )
        virtual_interfaces = vif_response.get("virtualInterfaces", [])

        # Collect Direct Connect Gateways
        try:
            dxgw_response = await self._simple_call(
                client=client,
                method_name="describe_direct_connect_gateways",
            )
            dx_gateways = dxgw_response.get("directConnectGateways", [])
        except Exception as e:
            logger.warning(f"Could not collect Direct Connect Gateways: {e}")
            dx_gateways = []

        # Group virtual interfaces by connection ID
        vifs_by_connection = {}
        for vif in virtual_interfaces:
            conn_id = vif.get("connectionId")
            if conn_id:
                if conn_id not in vifs_by_connection:
                    vifs_by_connection[conn_id] = []
                vifs_by_connection[conn_id].append(vif)

        # Normalize Direct Connect data
        normalized_dxs = []
        for dx in connections:
            connection_id = dx["connectionId"]
            vifs = vifs_by_connection.get(connection_id, [])

            # Parse virtual interfaces
            parsed_vifs = []
            for vif in vifs:
                parsed_vif = {
                    "virtual_interface_id": vif.get("virtualInterfaceId"),
                    "virtual_interface_name": vif.get("virtualInterfaceName"),
                    "virtual_interface_type": vif.get("virtualInterfaceType"),  # private, public, transit
                    "vlan": vif.get("vlan"),
                    "asn": vif.get("asn"),
                    "amazon_side_asn": vif.get("amazonSideAsn"),
                    "auth_key": vif.get("authKey"),
                    "amazon_address": vif.get("amazonAddress"),
                    "customer_address": vif.get("customerAddress"),
                    "address_family": vif.get("addressFamily"),  # ipv4 or ipv6
                    "virtual_interface_state": vif.get("virtualInterfaceState"),
                    "customer_router_config": vif.get("customerRouterConfig"),
                    "mtu": vif.get("mtu"),
                    "jumbo_frame_capable": vif.get("jumboFrameCapable"),
                    "virtual_gateway_id": vif.get("virtualGatewayId"),
                    "direct_connect_gateway_id": vif.get("directConnectGatewayId"),
                    "route_filter_prefixes": vif.get("routeFilterPrefixes", []),
                    "bgp_peers": vif.get("bgpPeers", []),
                    "region": vif.get("region"),
                    "aws_device_v2": vif.get("awsDeviceV2"),
                    "tags": [{"key": tag.get("key"), "value": tag.get("value")} for tag in vif.get("tags", [])],
                }
                parsed_vifs.append(parsed_vif)

            normalized_dx = {
                "id": connection_id,
                "connection_name": dx.get("connectionName"),
                "connection_state": dx.get("connectionState"),
                "region": dx.get("region"),
                "location": dx.get("location"),
                "bandwidth": dx.get("bandwidth"),
                "vlan": dx.get("vlan"),
                "partner_name": dx.get("partnerName"),
                "lag_id": dx.get("lagId"),
                "aws_device": dx.get("awsDevice"),
                "aws_device_v2": dx.get("awsDeviceV2"),
                "aws_logical_device_id": dx.get("awsLogicalDeviceId"),
                "has_logical_redundancy": dx.get("hasLogicalRedundancy"),
                "jumbo_frame_capable": dx.get("jumboFrameCapable"),
                "owner_account": dx.get("ownerAccount"),
                "provider_name": dx.get("providerName"),
                "encryption_mode": dx.get("encryptionMode"),
                "mac_sec_capable": dx.get("macSecCapable"),
                "port_encryption_status": dx.get("portEncryptionStatus"),
                # Virtual interfaces
                "virtual_interfaces": parsed_vifs,
                "virtual_interface_count": len(vifs),
                # Tags
                "tags": self._extract_dx_tags(dx.get("tags", [])),
                "name": dx.get("connectionName", ""),
                "resource_type": self.resource_type.value,
                # Enhanced metadata for enterprise analysis
                "is_available": dx.get("connectionState") == "available",
                "has_redundancy": dx.get("hasLogicalRedundancy") == "yes",
                "supports_jumbo_frames": dx.get("jumboFrameCapable", False),
                "supports_macsec": dx.get("macSecCapable", False),
                "vif_types": list(set(vif.get("virtual_interface_type") for vif in parsed_vifs)),
                "connected_gateways": list(
                    set(
                        vif.get("virtual_gateway_id") or vif.get("direct_connect_gateway_id")
                        for vif in parsed_vifs
                        if vif.get("virtual_gateway_id") or vif.get("direct_connect_gateway_id")
                    )
                ),
                "raw": dx,
            }
            normalized_dxs.append(normalized_dx)

        # Add Direct Connect Gateways as separate resources
        for dxgw in dx_gateways:
            normalized_dxgw = {
                "id": dxgw.get("directConnectGatewayId"),
                "name": dxgw.get("directConnectGatewayName"),
                "amazon_side_asn": dxgw.get("amazonSideAsn"),
                "owner_account": dxgw.get("ownerAccount"),
                "state": dxgw.get("directConnectGatewayState"),
                "state_change_error": dxgw.get("stateChangeError"),
                "resource_type": "direct_connect_gateway",
                "is_available": dxgw.get("directConnectGatewayState") == "available",
                "raw": dxgw,
            }
            normalized_dxs.append(normalized_dxgw)

        logger.info(
            f"Collected {len(connections)} Direct Connect connections and {len(dx_gateways)} gateways in {self.region}",
            extra={
                "connection_count": len(connections),
                "gateway_count": len(dx_gateways),
                "region": self.region,
            },
        )

        return normalized_dxs

    def _extract_dx_tags(self, tags: List[Dict[str, str]]) -> Dict[str, str]:
        """Extract Direct Connect tags into a dictionary."""
        if not tags:
            return {}
        return {tag.get("key", ""): tag.get("value", "") for tag in tags}
