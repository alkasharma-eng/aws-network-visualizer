"""
Lambda handler for anomaly analysis.

This function analyzes network topology for anomalies and
security issues using AI-powered detection.
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict

# Add src to path
sys.path.insert(0, "/opt/python")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from src.ai_analysis.anomaly_detector import AnomalyDetector
from src.collectors.collector_manager import CollectorManager
from src.core.logging import setup_logging, get_logger, set_request_id
from src.graph.analyzer import GraphAnalyzer
from src.graph.builder import GraphBuilder
from src.storage.dynamodb_repository import DynamoDBRepository
from src.storage.s3_repository import S3Repository

# Initialize logging
setup_logging()
logger = get_logger(__name__)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for anomaly analysis.

    Args:
        event: Lambda event (can be triggered by discovery completion)
        context: Lambda context

    Returns:
        Response with analysis results
    """
    request_id = context.request_id if context else "local"
    set_request_id(request_id)

    logger.info(
        "Starting anomaly analysis",
        extra={"request_id": request_id, "event": event},
    )

    try:
        # Get region and VPC from event or environment
        region = event.get("region", os.environ.get("AWS_REGION", "us-east-1"))
        vpc_id = event.get("vpc_id")

        # Option 1: Load from storage
        if vpc_id:
            logger.info(f"Loading topology for {region}/{vpc_id}")
            dynamodb_repo = DynamoDBRepository()
            topology_record = dynamodb_repo.get_latest_topology(region, vpc_id)

            if not topology_record:
                raise ValueError(f"No topology found for {region}/{vpc_id}")

            topology_data = topology_record["topology_data"]

            # Rebuild graph from stored data
            # Note: In production, implement graph deserialization
            manager = CollectorManager(regions=[region])
            results = asyncio.run(manager.collect_all())

        # Option 2: Run fresh discovery
        else:
            logger.info("Running fresh discovery for analysis")
            regions = event.get("regions", [region])
            manager = CollectorManager(regions=regions)
            results = asyncio.run(manager.collect_all())

        # Build graph
        builder = GraphBuilder()
        network_graph = builder.build_graph(results)

        # Analyze topology
        analyzer = GraphAnalyzer(network_graph)
        analysis = analyzer.analyze()

        # Detect anomalies
        enable_ai = event.get("enable_ai", True)
        detector = AnomalyDetector(network_graph, analyzer, enable_ai=enable_ai)
        anomalies = detector.detect_all_anomalies()

        # Generate report
        report = detector.generate_report(anomalies)

        # Store analysis results in S3
        s3_repo = S3Repository()
        analysis_data = {
            "analysis": analysis,
            "anomaly_report": report,
        }

        # Save to S3
        if vpc_id:
            key = f"analyses/{region}/{vpc_id}/{request_id}.json"
        else:
            key = f"analyses/full/{region}/{request_id}.json"

        s3_repo.client.put_object(
            Bucket=s3_repo.bucket_name,
            Key=key,
            Body=json.dumps(analysis_data, indent=2, default=str),
            ContentType="application/json",
        )

        logger.info(
            f"Analysis completed: {report['total_anomalies']} anomalies detected",
            extra={
                "total_anomalies": report["total_anomalies"],
                "by_severity": report["by_severity"],
            },
        )

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Analysis completed successfully",
                    "summary": {
                        "total_anomalies": report["total_anomalies"],
                        "by_severity": report["by_severity"],
                        "analysis_location": f"s3://{s3_repo.bucket_name}/{key}",
                    },
                    "request_id": request_id,
                }
            ),
        }

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)

        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "message": f"Analysis failed: {str(e)}",
                    "request_id": request_id,
                }
            ),
        }


# For local testing
if __name__ == "__main__":
    test_event = {"regions": ["us-east-1"], "enable_ai": True}

    class MockContext:
        request_id = "local-test"
        function_name = "analysis-function"

    response = handler(test_event, MockContext())
    print(json.dumps(response, indent=2))
