"""
Integration tests for end-to-end workflows.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.collectors.collector_manager import CollectorManager
from src.graph.builder import GraphBuilder
from src.graph.analyzer import GraphAnalyzer
from src.ai_analysis.anomaly_detector import AnomalyDetector


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_discovery_to_analysis(self, mock_aws):
        """Test complete flow from discovery to analysis."""
        # Step 1: Discovery
        manager = CollectorManager(regions=["us-east-1"])

        # Mock collector results
        mock_results = {
            "us-east-1": []
        }

        with patch.object(manager, "collect_all", return_value=mock_results):
            results = await manager.collect_all()

            assert isinstance(results, dict)

        # Step 2: Build graph
        builder = GraphBuilder()
        network_graph = builder.build_graph(results)

        assert network_graph is not None

        # Step 3: Analyze
        analyzer = GraphAnalyzer(network_graph)
        analysis = analyzer.analyze()

        assert "basic_metrics" in analysis
        assert "connectivity" in analysis

        # Step 4: Detect anomalies (without AI)
        detector = AnomalyDetector(network_graph, analyzer, enable_ai=False)
        anomalies = detector.detect_all_anomalies()

        assert isinstance(anomalies, list)
