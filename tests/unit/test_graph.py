"""
Unit tests for graph engine.
"""

import pytest
import networkx as nx

from src.collectors.base import CollectorResult
from src.core.constants import ResourceType
from src.graph.builder import GraphBuilder, NetworkGraph
from src.graph.analyzer import GraphAnalyzer


class TestGraphBuilder:
    """Test graph builder."""

    def test_build_empty_graph(self):
        """Test building graph with no resources."""
        builder = GraphBuilder()
        results_by_region = {}

        graph = builder.build_graph(results_by_region)

        assert isinstance(graph, NetworkGraph)
        assert graph.node_count == 0
        assert graph.edge_count == 0

    def test_build_graph_with_vpcs(self):
        """Test building graph with VPCs."""
        builder = GraphBuilder()

        vpc_result = CollectorResult(
            resource_type=ResourceType.VPC,
            region="us-east-1",
            resources=[
                {
                    "id": "vpc-123",
                    "cidr_block": "10.0.0.0/16",
                    "name": "TestVPC",
                    "region": "us-east-1",
                }
            ],
            success=True,
        )

        results_by_region = {"us-east-1": [vpc_result]}

        graph = builder.build_graph(results_by_region)

        assert graph.node_count == 1
        assert "vpc-123" in graph.graph.nodes
        assert graph.graph.nodes["vpc-123"]["resource_type"] == "vpc"

    def test_build_graph_with_relationships(self):
        """Test building graph with VPC->Subnet relationships."""
        builder = GraphBuilder()

        vpc_result = CollectorResult(
            resource_type=ResourceType.VPC,
            region="us-east-1",
            resources=[
                {
                    "id": "vpc-123",
                    "cidr_block": "10.0.0.0/16",
                    "region": "us-east-1",
                }
            ],
            success=True,
        )

        subnet_result = CollectorResult(
            resource_type=ResourceType.SUBNET,
            region="us-east-1",
            resources=[
                {
                    "id": "subnet-456",
                    "vpc_id": "vpc-123",
                    "cidr_block": "10.0.1.0/24",
                    "region": "us-east-1",
                }
            ],
            success=True,
        )

        results_by_region = {"us-east-1": [vpc_result, subnet_result]}

        graph = builder.build_graph(results_by_region)

        assert graph.node_count == 2
        assert graph.edge_count == 1
        assert graph.graph.has_edge("vpc-123", "subnet-456")


class TestGraphAnalyzer:
    """Test graph analyzer."""

    def test_basic_metrics(self):
        """Test basic graph metrics."""
        # Create simple graph
        G = nx.DiGraph()
        G.add_node("vpc-1", resource_type="vpc")
        G.add_node("subnet-1", resource_type="subnet", vpc_id="vpc-1")
        G.add_edge("vpc-1", "subnet-1", relationship="contains")

        network_graph = NetworkGraph(graph=G)
        analyzer = GraphAnalyzer(network_graph)

        metrics = analyzer.get_basic_metrics()

        assert metrics["total_nodes"] == 2
        assert metrics["total_edges"] == 1

    def test_find_isolated_resources(self):
        """Test finding isolated resources."""
        G = nx.DiGraph()
        G.add_node("vpc-1", resource_type="vpc")
        G.add_node("vpc-2", resource_type="vpc")  # Isolated
        G.add_node("subnet-1", resource_type="subnet", vpc_id="vpc-1")
        G.add_edge("vpc-1", "subnet-1")

        network_graph = NetworkGraph(graph=G)
        analyzer = GraphAnalyzer(network_graph)

        isolated = analyzer.find_isolated_resources()

        assert len(isolated) == 1
        assert isolated[0]["id"] == "vpc-2"

    def test_security_analysis(self):
        """Test security posture analysis."""
        G = nx.DiGraph()

        # Add security group with overly permissive rule
        G.add_node(
            "sg-1",
            resource_type="security_group",
            data={
                "ingress_rules": [
                    {
                        "ip_ranges": [{"cidr": "0.0.0.0/0"}],
                        "from_port": 22,
                        "to_port": 22,
                        "ip_protocol": "tcp",
                    }
                ]
            },
        )

        network_graph = NetworkGraph(graph=G)
        analyzer = GraphAnalyzer(network_graph)

        security = analyzer.analyze_security_posture()

        assert security["issues_found"] > 0
        assert any(
            issue["issue_type"] == "overly_permissive_ingress"
            for issue in security["issues"]
        )
