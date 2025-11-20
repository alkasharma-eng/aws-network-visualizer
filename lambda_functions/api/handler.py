"""
Lambda handler for API Gateway.

This function provides a REST API for querying topology data.
"""

import json
import os
import sys
from typing import Any, Dict

# Add src to path
sys.path.insert(0, "/opt/python")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from src.core.logging import setup_logging, get_logger, set_request_id
from src.storage.dynamodb_repository import DynamoDBRepository
from src.storage.s3_repository import S3Repository
from src.storage.cache_repository import CacheRepository

# Initialize logging
setup_logging()
logger = get_logger(__name__)

# Initialize repositories
dynamodb_repo = DynamoDBRepository()
s3_repo = S3Repository()
cache_repo = CacheRepository()


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    API Gateway Lambda handler.

    Routes:
        GET /topology/{region}/{vpc_id} - Get latest topology
        GET /topology/{region}/{vpc_id}/history - Get topology history
        GET /analyses/{region}/{vpc_id}/latest - Get latest analysis

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    request_id = context.request_id if context else "local"
    set_request_id(request_id)

    # Parse request
    http_method = event.get("httpMethod", "GET")
    path = event.get("path", "")
    path_params = event.get("pathParameters", {})
    query_params = event.get("queryStringParameters") or {}

    logger.info(
        f"API request: {http_method} {path}",
        extra={"method": http_method, "path": path, "request_id": request_id},
    )

    try:
        # Route handling
        if path.startswith("/topology/"):
            return handle_topology_request(
                path_params, query_params, http_method, request_id
            )
        elif path.startswith("/analyses/"):
            return handle_analysis_request(
                path_params, query_params, http_method, request_id
            )
        elif path == "/health":
            return create_response(200, {"status": "healthy", "request_id": request_id})
        else:
            return create_response(404, {"error": "Not found", "path": path})

    except Exception as e:
        logger.error(f"API request failed: {e}", exc_info=True)
        return create_response(
            500, {"error": f"Internal server error: {str(e)}", "request_id": request_id}
        )


def handle_topology_request(
    path_params: Dict[str, str],
    query_params: Dict[str, str],
    method: str,
    request_id: str,
) -> Dict[str, Any]:
    """Handle topology-related requests."""
    region = path_params.get("region")
    vpc_id = path_params.get("vpc_id")

    if not region or not vpc_id:
        return create_response(400, {"error": "Missing region or vpc_id"})

    # Check if history is requested
    if "history" in query_params or path_params.get("action") == "history":
        limit = int(query_params.get("limit", 10))
        history = dynamodb_repo.get_topology_history(region, vpc_id, limit)

        return create_response(
            200,
            {
                "region": region,
                "vpc_id": vpc_id,
                "history": [
                    {
                        "timestamp": item["SK"],
                        "node_count": item["topology_data"].get("node_count", 0),
                        "edge_count": item["topology_data"].get("edge_count", 0),
                    }
                    for item in history
                ],
                "request_id": request_id,
            },
        )

    # Get latest topology
    # Try cache first
    cached = cache_repo.get_cached_topology(region, vpc_id)
    if cached:
        logger.info("Returning cached topology")
        return create_response(
            200, {"region": region, "vpc_id": vpc_id, "topology": cached, "cached": True}
        )

    # Load from DynamoDB
    topology = dynamodb_repo.get_latest_topology(region, vpc_id)

    if not topology:
        return create_response(404, {"error": "Topology not found"})

    # Cache the result
    cache_repo.cache_topology(region, vpc_id, topology["topology_data"])

    return create_response(
        200,
        {
            "region": region,
            "vpc_id": vpc_id,
            "topology": topology["topology_data"],
            "cached": False,
            "request_id": request_id,
        },
    )


def handle_analysis_request(
    path_params: Dict[str, str],
    query_params: Dict[str, str],
    method: str,
    request_id: str,
) -> Dict[str, Any]:
    """Handle analysis-related requests."""
    region = path_params.get("region")
    vpc_id = path_params.get("vpc_id")

    if not region or not vpc_id:
        return create_response(400, {"error": "Missing region or vpc_id"})

    # List analyses for this VPC
    objects = s3_repo.list_topologies(region, vpc_id)

    # Filter for analysis files
    analysis_files = [obj for obj in objects if "analyses/" in obj["key"]]

    if not analysis_files:
        return create_response(404, {"error": "No analyses found"})

    # Get the latest
    latest = max(analysis_files, key=lambda x: x["last_modified"])

    # Download the analysis
    analysis_data = s3_repo.download_topology(latest["key"])

    return create_response(
        200,
        {
            "region": region,
            "vpc_id": vpc_id,
            "analysis": analysis_data,
            "timestamp": latest["last_modified"].isoformat(),
            "request_id": request_id,
        },
    )


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create API Gateway response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
        "body": json.dumps(body, default=str),
    }


# For local testing
if __name__ == "__main__":
    test_event = {
        "httpMethod": "GET",
        "path": "/health",
        "pathParameters": {},
        "queryStringParameters": {},
    }

    class MockContext:
        request_id = "local-test"

    response = handler(test_event, MockContext())
    print(json.dumps(response, indent=2))
