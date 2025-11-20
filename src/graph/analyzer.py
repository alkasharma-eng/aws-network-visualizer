"""
Graph analyzer for network topology analysis.

This module provides analysis capabilities for network graphs including
connectivity analysis, path finding, and topology pattern detection.
"""

from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx

from src.core.constants import ResourceType, RelationshipType
from src.core.logging import get_logger
from src.graph.builder import NetworkGraph

logger = get_logger(__name__)


class GraphAnalyzer:
    """
    Analyzes network topology graphs for insights and anomalies.
    """

    def __init__(self, network_graph: NetworkGraph):
        """
        Initialize graph analyzer.

        Args:
            network_graph: NetworkGraph to analyze
        """
        self.network_graph = network_graph
        self.graph = network_graph.graph
        logger.info("Initialized GraphAnalyzer")

    def analyze(self) -> Dict[str, Any]:
        """
        Perform comprehensive graph analysis.

        Returns:
            Dictionary containing analysis results
        """
        logger.info("Starting comprehensive graph analysis")

        analysis = {
            "basic_metrics": self.get_basic_metrics(),
            "connectivity": self.analyze_connectivity(),
            "isolated_resources": self.find_isolated_resources(),
            "vpc_analysis": self.analyze_vpcs(),
            "security_analysis": self.analyze_security_posture(),
            "subnet_analysis": self.analyze_subnets(),
        }

        logger.info("Completed graph analysis")
        return analysis

    def get_basic_metrics(self) -> Dict[str, Any]:
        """
        Get basic graph metrics.

        Returns:
            Dictionary of basic metrics
        """
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "resource_counts": self.network_graph.resource_counts,
            "density": nx.density(self.graph),
            "is_connected": nx.is_weakly_connected(self.graph),
        }

    def analyze_connectivity(self) -> Dict[str, Any]:
        """
        Analyze graph connectivity.

        Returns:
            Dictionary with connectivity metrics
        """
        # Find weakly connected components
        components = list(nx.weakly_connected_components(self.graph))

        return {
            "component_count": len(components),
            "largest_component_size": len(max(components, key=len)) if components else 0,
            "smallest_component_size": len(min(components, key=len)) if components else 0,
            "is_strongly_connected": nx.is_strongly_connected(self.graph),
        }

    def find_isolated_resources(self) -> List[Dict[str, Any]]:
        """
        Find resources with no connections.

        Returns:
            List of isolated resource dictionaries
        """
        isolated = []

        for node_id, node_data in self.graph.nodes(data=True):
            in_degree = self.graph.in_degree(node_id)
            out_degree = self.graph.out_degree(node_id)

            if in_degree == 0 and out_degree == 0:
                isolated.append(
                    {
                        "id": node_id,
                        "resource_type": node_data.get("resource_type"),
                        "name": node_data.get("name", ""),
                        "region": node_data.get("region"),
                    }
                )

        logger.info(f"Found {len(isolated)} isolated resources")
        return isolated

    def analyze_vpcs(self) -> Dict[str, Any]:
        """
        Analyze VPC topology.

        Returns:
            Dictionary with VPC analysis
        """
        vpc_analysis = {}

        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get("resource_type") != ResourceType.VPC.value:
                continue

            # Count resources in this VPC
            subnets = self._get_vpc_subnets(node_id)
            instances = self._get_vpc_instances(node_id)
            igws = self._get_vpc_internet_gateways(node_id)

            vpc_analysis[node_id] = {
                "name": node_data.get("name", ""),
                "cidr_block": node_data.get("cidr_block"),
                "region": node_data.get("region"),
                "subnet_count": len(subnets),
                "instance_count": len(instances),
                "internet_gateway_count": len(igws),
                "has_internet_connectivity": len(igws) > 0,
                "subnets": subnets,
                "instances": instances,
            }

        return vpc_analysis

    def analyze_security_posture(self) -> Dict[str, Any]:
        """
        Analyze security-related aspects of the network.

        Returns:
            Dictionary with security analysis
        """
        security_issues = []

        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get("resource_type") != ResourceType.SECURITY_GROUP.value:
                continue

            sg_data = node_data.get("data", {})
            ingress_rules = sg_data.get("ingress_rules", [])

            # Check for overly permissive rules
            for rule in ingress_rules:
                for ip_range in rule.get("ip_ranges", []):
                    cidr = ip_range.get("cidr", "")
                    if cidr == "0.0.0.0/0":
                        security_issues.append(
                            {
                                "security_group_id": node_id,
                                "security_group_name": node_data.get("name", ""),
                                "issue_type": "overly_permissive_ingress",
                                "severity": "high",
                                "description": f"Security group allows ingress from 0.0.0.0/0 on ports {rule.get('from_port')}-{rule.get('to_port')}",
                                "protocol": rule.get("ip_protocol"),
                                "from_port": rule.get("from_port"),
                                "to_port": rule.get("to_port"),
                            }
                        )

        return {
            "total_security_groups": sum(
                1
                for _, data in self.graph.nodes(data=True)
                if data.get("resource_type") == ResourceType.SECURITY_GROUP.value
            ),
            "issues_found": len(security_issues),
            "issues": security_issues,
        }

    def analyze_subnets(self) -> Dict[str, Any]:
        """
        Analyze subnet configuration.

        Returns:
            Dictionary with subnet analysis
        """
        subnet_analysis = {}

        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get("resource_type") != ResourceType.SUBNET.value:
                continue

            # Count instances in subnet
            instances = list(self.graph.successors(node_id))
            instance_count = sum(
                1
                for inst_id in instances
                if self.graph.nodes[inst_id].get("resource_type")
                == ResourceType.EC2_INSTANCE.value
            )

            subnet_analysis[node_id] = {
                "name": node_data.get("name", ""),
                "cidr_block": node_data.get("cidr_block"),
                "availability_zone": node_data.get("availability_zone"),
                "vpc_id": node_data.get("vpc_id"),
                "instance_count": instance_count,
                "map_public_ip": node_data.get("map_public_ip_on_launch", False),
            }

        return subnet_analysis

    def _get_vpc_subnets(self, vpc_id: str) -> List[str]:
        """Get subnet IDs for a VPC."""
        subnets = []
        for successor in self.graph.successors(vpc_id):
            if (
                self.graph.nodes[successor].get("resource_type")
                == ResourceType.SUBNET.value
            ):
                subnets.append(successor)
        return subnets

    def _get_vpc_instances(self, vpc_id: str) -> List[str]:
        """Get EC2 instance IDs for a VPC."""
        instances = []
        # Get all subnets in VPC
        subnets = self._get_vpc_subnets(vpc_id)

        # Get instances in each subnet
        for subnet_id in subnets:
            for successor in self.graph.successors(subnet_id):
                if (
                    self.graph.nodes[successor].get("resource_type")
                    == ResourceType.EC2_INSTANCE.value
                ):
                    instances.append(successor)

        return instances

    def _get_vpc_internet_gateways(self, vpc_id: str) -> List[str]:
        """Get Internet Gateway IDs for a VPC."""
        igws = []
        for successor in self.graph.successors(vpc_id):
            if (
                self.graph.nodes[successor].get("resource_type")
                == ResourceType.INTERNET_GATEWAY.value
            ):
                igws.append(successor)
        return igws

    def find_path(self, source: str, target: str) -> Optional[List[str]]:
        """
        Find path between two resources.

        Args:
            source: Source resource ID
            target: Target resource ID

        Returns:
            List of node IDs forming the path, or None if no path exists
        """
        try:
            return nx.shortest_path(self.graph, source, target)
        except nx.NetworkXNoPath:
            return None

    def get_resource_dependencies(self, resource_id: str) -> Dict[str, List[str]]:
        """
        Get all dependencies for a resource.

        Args:
            resource_id: Resource ID to analyze

        Returns:
            Dictionary with incoming and outgoing dependencies
        """
        return {
            "depends_on": list(self.graph.predecessors(resource_id)),
            "depended_by": list(self.graph.successors(resource_id)),
        }

    def get_centrality_metrics(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate centrality metrics for all nodes.

        Returns:
            Dictionary mapping node IDs to centrality scores
        """
        return {
            "degree_centrality": nx.degree_centrality(self.graph),
            "betweenness_centrality": nx.betweenness_centrality(self.graph),
            "closeness_centrality": nx.closeness_centrality(self.graph),
        }
