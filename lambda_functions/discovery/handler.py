"""
Lambda handler for network discovery.

This function is triggered on a schedule (e.g., daily) to discover
and store network topology data.
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict

# Add src to path
sys.path.insert(0, "/opt/python")  # Lambda layer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from src.collectors.collector_manager import CollectorManager
from src.core.config import get_settings
from src.core.logging import setup_logging, get_logger, set_request_id
from src.graph.builder import GraphBuilder
from src.storage.dynamodb_repository import DynamoDBRepository
from src.storage.s3_repository import S3Repository

# Initialize logging
setup_logging()
logger = get_logger(__name__)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for scheduled network discovery.

    Args:
        event: Lambda event (EventBridge scheduled event)
        context: Lambda context

    Returns:
        Response with discovery results
    """
    # Set request ID from Lambda context
    request_id = context.request_id if context else "local"
    set_request_id(request_id)

    logger.info(
        "Starting scheduled network discovery",
        extra={"request_id": request_id, "event": event},
    )

    try:
        # Get configuration from environment or event
        regions = os.environ.get("AWS_REGIONS", "us-east-1").split(",")
        if "regions" in event:
            regions = event["regions"]

        # Run discovery
        manager = CollectorManager(regions=regions)
        results = asyncio.run(manager.collect_all())

        # Build graph
        builder = GraphBuilder()
        network_graph = builder.build_graph(results)

        # Get summary
        summary = manager.get_summary(results)

        # Store results
        dynamodb_repo = DynamoDBRepository()
        s3_repo = S3Repository()

        # Export graph
        graph_data = builder.export_to_dict(network_graph)

        # Store in DynamoDB and S3
        for region, region_results in results.items():
            for result in region_results:
                if result.success and result.resource_type.value == "vpc":
                    for vpc in result.resources:
                        vpc_id = vpc["id"]

                        # Save to DynamoDB
                        dynamodb_repo.save_topology(
                            region=region,
                            vpc_id=vpc_id,
                            topology_data=graph_data,
                            metadata=summary,
                        )

                        # Save to S3
                        s3_repo.upload_topology(
                            region=region,
                            vpc_id=vpc_id,
                            topology_data=graph_data,
                        )

        logger.info(
            "Discovery completed successfully",
            extra={
                "total_resources": summary["total_resources"],
                "regions": len(results),
            },
        )

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Discovery completed successfully",
                    "summary": summary,
                    "request_id": request_id,
                }
            ),
        }

    except Exception as e:
        logger.error(f"Discovery failed: {e}", exc_info=True)

        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "message": f"Discovery failed: {str(e)}",
                    "request_id": request_id,
                }
            ),
        }


# For local testing
if __name__ == "__main__":
    # Mock event and context
    test_event = {"regions": ["us-east-1"]}

    class MockContext:
        request_id = "local-test"
        function_name = "discovery-function"
        memory_limit_in_mb = 1024
        invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:discovery"

    response = handler(test_event, MockContext())
    print(json.dumps(response, indent=2))
