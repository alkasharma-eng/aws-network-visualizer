"""
Graph builder for constructing network topology graphs.

This module builds directed graphs from collected AWS resources,
establishing relationships and dependencies between network components.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx

from src.collectors.base import CollectorResult
from src.core.constants import RelationshipType, ResourceType
from src.core.logging import get_logger
from src.observability.metrics import get_metrics_publisher, MetricsTimer
from src.observability.tracing import trace_function

logger = get_logger(__name__)


@dataclass
class NetworkGraph:
    """
    Network topology graph with metadata.
    """

    graph: nx.DiGraph
    metadata: Dict[str, Any] = field(default_factory=dict)
    build_time: float = 0.0
    node_count: int = 0
    edge_count: int = 0
    resource_counts: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        """Update counts from graph."""
        self.node_count = self.graph.number_of_nodes()
        self.edge_count = self.graph.number_of_edges()


class GraphBuilder:
    """
    Builds network topology graphs from collected AWS resources.
    """

    def __init__(self):
        """Initialize graph builder."""
        self.metrics = get_metrics_publisher()
        logger.info("Initialized GraphBuilder")

    @trace_function(name="build_graph", capture_args=False)
    def build_graph(
        self,
        results_by_region: Dict[str, List[CollectorResult]],
    ) -> NetworkGraph:
        """
        Build a network topology graph from collector results.

        Args:
            results_by_region: Dictionary mapping regions to collector results

        Returns:
            NetworkGraph with complete topology

        Raises:
            Exception: If graph building fails
        """
        start_time = time.time()

        logger.info(
            f"Building network graph from {len(results_by_region)} regions",
            extra={"regions": len(results_by_region)},
        )

        with MetricsTimer(self.metrics, "graph_build_duration"):
            # Create directed graph
            graph = nx.DiGraph()

            # Track resource counts
            resource_counts = {}

            # Add nodes for each resource
            for region, results in results_by_region.items():
                for result in results:
                    if not result.success:
                        continue

                    resource_type = result.resource_type.value
                    if resource_type not in resource_counts:
                        resource_counts[resource_type] = 0
                    resource_counts[resource_type] += len(result.resources)

                    # Add nodes based on resource type
                    if result.resource_type == ResourceType.VPC:
                        self._add_vpc_nodes(graph, result.resources)
                    elif result.resource_type == ResourceType.SUBNET:
                        self._add_subnet_nodes(graph, result.resources)
                    elif result.resource_type == ResourceType.EC2_INSTANCE:
                        self._add_ec2_nodes(graph, result.resources)
                    elif result.resource_type == ResourceType.INTERNET_GATEWAY:
                        self._add_igw_nodes(graph, result.resources)
                    elif result.resource_type == ResourceType.SECURITY_GROUP:
                        self._add_security_group_nodes(graph, result.resources)

            # Build relationships between resources
            self._build_relationships(graph)

            # Create network graph object
            network_graph = NetworkGraph(
                graph=graph,
                build_time=time.time() - start_time,
                resource_counts=resource_counts,
                metadata={
                    "regions": list(results_by_region.keys()),
                    "build_timestamp": time.time(),
                },
            )

        logger.info(
            f"Built graph with {network_graph.node_count} nodes and {network_graph.edge_count} edges",
            extra={
                "nodes": network_graph.node_count,
                "edges": network_graph.edge_count,
                "duration": network_graph.build_time,
            },
        )

        return network_graph

    def _add_vpc_nodes(self, graph: nx.DiGraph, vpcs: List[Dict[str, Any]]) -> None:
        """Add VPC nodes to graph."""
        for vpc in vpcs:
            graph.add_node(
                vpc["id"],
                resource_type=ResourceType.VPC.value,
                name=vpc.get("name", ""),
                cidr_block=vpc.get("cidr_block"),
                region=vpc.get("region"),
                tags=vpc.get("tags", {}),
                data=vpc,
            )

    def _add_subnet_nodes(
        self, graph: nx.DiGraph, subnets: List[Dict[str, Any]]
    ) -> None:
        """Add Subnet nodes to graph."""
        for subnet in subnets:
            graph.add_node(
                subnet["id"],
                resource_type=ResourceType.SUBNET.value,
                name=subnet.get("name", ""),
                cidr_block=subnet.get("cidr_block"),
                availability_zone=subnet.get("availability_zone"),
                region=subnet.get("region"),
                vpc_id=subnet.get("vpc_id"),
                tags=subnet.get("tags", {}),
                data=subnet,
            )

    def _add_ec2_nodes(
        self, graph: nx.DiGraph, instances: List[Dict[str, Any]]
    ) -> None:
        """Add EC2 instance nodes to graph."""
        for instance in instances:
            graph.add_node(
                instance["id"],
                resource_type=ResourceType.EC2_INSTANCE.value,
                name=instance.get("name", ""),
                instance_type=instance.get("instance_type"),
                state=instance.get("state"),
                private_ip=instance.get("private_ip"),
                public_ip=instance.get("public_ip"),
                region=instance.get("region"),
                vpc_id=instance.get("vpc_id"),
                subnet_id=instance.get("subnet_id"),
                tags=instance.get("tags", {}),
                data=instance,
            )

    def _add_igw_nodes(self, graph: nx.DiGraph, igws: List[Dict[str, Any]]) -> None:
        """Add Internet Gateway nodes to graph."""
        for igw in igws:
            graph.add_node(
                igw["id"],
                resource_type=ResourceType.INTERNET_GATEWAY.value,
                name=igw.get("name", ""),
                attached_vpcs=igw.get("attached_vpc_ids", []),
                region=igw.get("region"),
                tags=igw.get("tags", {}),
                data=igw,
            )

    def _add_security_group_nodes(
        self, graph: nx.DiGraph, security_groups: List[Dict[str, Any]]
    ) -> None:
        """Add Security Group nodes to graph."""
        for sg in security_groups:
            graph.add_node(
                sg["id"],
                resource_type=ResourceType.SECURITY_GROUP.value,
                name=sg.get("name", ""),
                description=sg.get("description"),
                vpc_id=sg.get("vpc_id"),
                region=sg.get("region"),
                ingress_rules=sg.get("ingress_rules", []),
                egress_rules=sg.get("egress_rules", []),
                tags=sg.get("tags", {}),
                data=sg,
            )

    def _build_relationships(self, graph: nx.DiGraph) -> None:
        """
        Build relationships (edges) between resources.

        Args:
            graph: NetworkX graph to add edges to
        """
        logger.debug("Building relationships between resources")

        # VPC -> Subnet relationships
        self._connect_vpcs_to_subnets(graph)

        # Subnet -> EC2 relationships
        self._connect_subnets_to_instances(graph)

        # VPC -> Internet Gateway relationships
        self._connect_vpcs_to_igws(graph)

        # Security Group relationships
        self._connect_security_groups(graph)

        logger.debug(f"Built {graph.number_of_edges()} relationships")

    def _connect_vpcs_to_subnets(self, graph: nx.DiGraph) -> None:
        """Connect VPCs to their subnets."""
        for node_id, node_data in graph.nodes(data=True):
            if node_data.get("resource_type") == ResourceType.SUBNET.value:
                vpc_id = node_data.get("vpc_id")
                if vpc_id and graph.has_node(vpc_id):
                    graph.add_edge(
                        vpc_id,
                        node_id,
                        relationship=RelationshipType.CONTAINS.value,
                        label="contains",
                    )

    def _connect_subnets_to_instances(self, graph: nx.DiGraph) -> None:
        """Connect subnets to their EC2 instances."""
        for node_id, node_data in graph.nodes(data=True):
            if node_data.get("resource_type") == ResourceType.EC2_INSTANCE.value:
                subnet_id = node_data.get("subnet_id")
                if subnet_id and graph.has_node(subnet_id):
                    graph.add_edge(
                        subnet_id,
                        node_id,
                        relationship=RelationshipType.HOSTS.value,
                        label="hosts",
                    )

    def _connect_vpcs_to_igws(self, graph: nx.DiGraph) -> None:
        """Connect VPCs to their internet gateways."""
        for node_id, node_data in graph.nodes(data=True):
            if node_data.get("resource_type") == ResourceType.INTERNET_GATEWAY.value:
                attached_vpcs = node_data.get("attached_vpcs", [])
                for vpc_id in attached_vpcs:
                    if graph.has_node(vpc_id):
                        graph.add_edge(
                            vpc_id,
                            node_id,
                            relationship=RelationshipType.ATTACHED_TO.value,
                            label="attached_to",
                        )

    def _connect_security_groups(self, graph: nx.DiGraph) -> None:
        """Connect resources to their security groups."""
        for node_id, node_data in graph.nodes(data=True):
            if node_data.get("resource_type") == ResourceType.EC2_INSTANCE.value:
                instance_data = node_data.get("data", {})
                security_groups = instance_data.get("security_groups", [])

                for sg in security_groups:
                    sg_id = sg.get("id")
                    if sg_id and graph.has_node(sg_id):
                        graph.add_edge(
                            sg_id,
                            node_id,
                            relationship=RelationshipType.PROTECTS.value,
                            label="protects",
                        )

    def export_to_dict(self, network_graph: NetworkGraph) -> Dict[str, Any]:
        """
        Export graph to dictionary format.

        Args:
            network_graph: NetworkGraph to export

        Returns:
            Dictionary representation of the graph
        """
        graph = network_graph.graph

        nodes = []
        for node_id, node_data in graph.nodes(data=True):
            node_dict = {
                "id": node_id,
                "resource_type": node_data.get("resource_type"),
                "name": node_data.get("name", ""),
                "region": node_data.get("region"),
            }
            # Add resource-specific fields
            for key, value in node_data.items():
                if key not in ["data", "tags"] and value is not None:
                    node_dict[key] = value
            nodes.append(node_dict)

        edges = []
        for source, target, edge_data in graph.edges(data=True):
            edges.append(
                {
                    "source": source,
                    "target": target,
                    "relationship": edge_data.get("relationship"),
                    "label": edge_data.get("label", ""),
                }
            )

        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": network_graph.metadata,
            "node_count": network_graph.node_count,
            "edge_count": network_graph.edge_count,
            "resource_counts": network_graph.resource_counts,
        }
