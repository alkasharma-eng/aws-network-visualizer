"""
Constants and enumerations used throughout the application.
"""

from enum import Enum


class ResourceType(str, Enum):
    """AWS resource types supported by the collector."""

    VPC = "vpc"
    SUBNET = "subnet"
    EC2_INSTANCE = "ec2_instance"
    INTERNET_GATEWAY = "internet_gateway"
    NAT_GATEWAY = "nat_gateway"
    TRANSIT_GATEWAY = "transit_gateway"
    SECURITY_GROUP = "security_group"
    ROUTE_TABLE = "route_table"
    NETWORK_ACL = "network_acl"
    VPC_PEERING = "vpc_peering"
    VPN_CONNECTION = "vpn_connection"
    DIRECT_CONNECT = "direct_connect"
    LOAD_BALANCER = "load_balancer"
    RDS_INSTANCE = "rds_instance"
    LAMBDA_ENI = "lambda_eni"


class RelationshipType(str, Enum):
    """Types of relationships between resources."""

    CONTAINS = "contains"
    HOSTS = "hosts"
    CONNECTS_TO = "connects_to"
    ROUTES_TO = "routes_to"
    ATTACHED_TO = "attached_to"
    PROTECTS = "protects"
    PEERS_WITH = "peers_with"
    DEPENDS_ON = "depends_on"


class VisualizationType(str, Enum):
    """Supported visualization output formats."""

    PNG = "png"
    SVG = "svg"
    HTML = "html"
    JSON = "json"


class AnomalyType(str, Enum):
    """Types of anomalies detected by AI analysis."""

    SECURITY_GROUP_MISCONFIGURATION = "security_group_misconfiguration"
    NETWORK_SEGMENTATION_VIOLATION = "network_segmentation_violation"
    ROUTING_ANOMALY = "routing_anomaly"
    COMPLIANCE_VIOLATION = "compliance_violation"
    COST_OPTIMIZATION = "cost_optimization"
    ORPHANED_RESOURCE = "orphaned_resource"
    MISSING_ENCRYPTION = "missing_encryption"
    MISSING_LOGGING = "missing_logging"


class SeverityLevel(str, Enum):
    """Severity levels for anomalies and issues."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class MetricName(str, Enum):
    """CloudWatch metric names."""

    # Discovery metrics
    DISCOVERY_DURATION = "DiscoveryDuration"
    RESOURCE_COUNT = "ResourceCount"
    API_CALL_COUNT = "APICallCount"
    API_CALL_SUCCESS = "APICallSuccess"
    API_CALL_FAILURE = "APICallFailure"

    # Error metrics
    ERROR_COUNT = "ErrorCount"
    RETRY_COUNT = "RetryCount"
    RATE_LIMIT_COUNT = "RateLimitCount"

    # Performance metrics
    COLLECTOR_DURATION = "CollectorDuration"
    GRAPH_BUILD_DURATION = "GraphBuildDuration"
    VISUALIZATION_DURATION = "VisualizationDuration"

    # AI analysis metrics
    AI_ANALYSIS_DURATION = "AIAnalysisDuration"
    BEDROCK_TOKEN_USAGE = "BedrockTokenUsage"
    ANOMALY_COUNT = "AnomalyCount"

    # Storage metrics
    DYNAMODB_READ_LATENCY = "DynamoDBReadLatency"
    DYNAMODB_WRITE_LATENCY = "DynamoDBWriteLatency"
    S3_UPLOAD_DURATION = "S3UploadDuration"
    CACHE_HIT_RATE = "CacheHitRate"


class MetricUnit(str, Enum):
    """CloudWatch metric units."""

    SECONDS = "Seconds"
    MILLISECONDS = "Milliseconds"
    COUNT = "Count"
    PERCENT = "Percent"
    BYTES = "Bytes"


# AWS API rate limits (requests per second)
AWS_API_RATE_LIMITS = {
    "ec2:DescribeVpcs": 100,
    "ec2:DescribeSubnets": 100,
    "ec2:DescribeInstances": 100,
    "ec2:DescribeSecurityGroups": 100,
    "ec2:DescribeRouteTables": 100,
    "ec2:DescribeNetworkAcls": 100,
    "ec2:DescribeInternetGateways": 100,
    "ec2:DescribeNatGateways": 100,
    "ec2:DescribeTransitGateways": 50,
    "ec2:DescribeVpcPeeringConnections": 100,
    "ec2:DescribeVpnConnections": 100,
    "elbv2:DescribeLoadBalancers": 100,
    "rds:DescribeDBInstances": 100,
}

# Maximum resources to collect per region (safety limits)
MAX_RESOURCES_PER_TYPE = 10000

# Timeout values (seconds)
DEFAULT_API_TIMEOUT = 30
DEFAULT_LAMBDA_TIMEOUT = 900  # 15 minutes
DEFAULT_CACHE_TTL = 3600  # 1 hour

# Retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BASE_DELAY = 1.0
DEFAULT_RETRY_MAX_DELAY = 60.0

# Batch sizes for parallel processing
DEFAULT_BATCH_SIZE = 100
MAX_CONCURRENT_REQUESTS = 10

# AI Analysis
BEDROCK_MAX_TOKENS = 4096
BEDROCK_TEMPERATURE = 0.0

# Visualization
DEFAULT_GRAPH_WIDTH = 1920
DEFAULT_GRAPH_HEIGHT = 1080
DEFAULT_NODE_SIZE = 1000
DEFAULT_FONT_SIZE = 10
