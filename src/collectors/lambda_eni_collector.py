"""
Lambda ENI collector.

Collects Lambda functions with VPC configurations and their associated
Elastic Network Interfaces (ENIs) for serverless network topology analysis.
"""

from typing import Any, Dict, List, Optional

from src.collectors.base import BaseCollector
from src.core.constants import ResourceType
from src.core.logging import get_logger

logger = get_logger(__name__)


class LambdaENICollector(BaseCollector):
    """
    Collector for AWS Lambda ENI resources.

    Collects Lambda functions configured with VPC access and their
    associated network interfaces. Critical for serverless architecture
    network topology visualization.
    """

    def __init__(
        self,
        region: str,
        profile: Optional[str] = None,
        rate_limit: Optional[float] = None,
        vpc_id: Optional[str] = None,
    ):
        """
        Initialize Lambda ENI collector.

        Args:
            region: AWS region
            profile: AWS profile
            rate_limit: Rate limit in requests/second
            vpc_id: Optional VPC ID to filter Lambda functions
        """
        super().__init__(region, profile, rate_limit)
        self.vpc_id = vpc_id

    @property
    def resource_type(self) -> ResourceType:
        """Resource type for this collector."""
        return ResourceType.LAMBDA_ENI

    @property
    def service_name(self) -> str:
        """AWS service name."""
        return "lambda"

    async def collect_resources(self) -> List[Dict[str, Any]]:
        """
        Collect Lambda ENI resources.

        Returns:
            List of Lambda function dictionaries with VPC configuration

        Raises:
            CollectorException: If collection fails
        """
        client = self.get_client()

        # Collect all Lambda functions with pagination
        functions = await self._paginated_call(
            client=client,
            method_name="list_functions",
            result_key="Functions",
        )

        # Filter to only VPC-enabled functions
        vpc_functions = [func for func in functions if func.get("VpcConfig", {}).get("VpcId")]

        # Further filter by specific VPC if requested
        if self.vpc_id:
            vpc_functions = [
                func for func in vpc_functions if func.get("VpcConfig", {}).get("VpcId") == self.vpc_id
            ]

        # Get ENI information from EC2 for Lambda functions
        ec2_client = self.get_client("ec2")
        lambda_enis = []

        if vpc_functions:
            # Get all ENIs with Lambda description
            try:
                enis = await self._paginated_call(
                    client=ec2_client,
                    method_name="describe_network_interfaces",
                    result_key="NetworkInterfaces",
                    Filters=[
                        {"Name": "description", "Values": ["*AWS Lambda VPC ENI*"]},
                    ],
                )
            except Exception as e:
                logger.warning(f"Could not collect Lambda ENIs: {e}")
                enis = []

            # Group ENIs by function name (extracted from description)
            enis_by_function = {}
            for eni in enis:
                description = eni.get("Description", "")
                # Description format: "AWS Lambda VPC ENI-{function-name}-{hash}"
                if "AWS Lambda VPC ENI" in description:
                    # Try to extract function name from ENI
                    enis_by_function.setdefault("unknown", []).append(eni)

            # Normalize Lambda function data with VPC configuration
            normalized_functions = []
            for func in vpc_functions:
                vpc_config = func.get("VpcConfig", {})
                environment = func.get("Environment", {})

                # Try to find associated ENIs
                function_name = func.get("FunctionName")
                associated_enis = []

                # Get ENIs that match this function's subnets and security groups
                func_subnet_ids = set(vpc_config.get("SubnetIds", []))
                func_sg_ids = set(vpc_config.get("SecurityGroupIds", []))

                for eni in enis:
                    eni_subnet = eni.get("SubnetId")
                    eni_groups = {sg.get("GroupId") for sg in eni.get("Groups", [])}

                    if eni_subnet in func_subnet_ids and eni_groups.intersection(func_sg_ids):
                        associated_enis.append({
                            "network_interface_id": eni.get("NetworkInterfaceId"),
                            "subnet_id": eni.get("SubnetId"),
                            "vpc_id": eni.get("VpcId"),
                            "availability_zone": eni.get("AvailabilityZone"),
                            "private_ip_address": eni.get("PrivateIpAddress"),
                            "private_ip_addresses": [
                                addr.get("PrivateIpAddress") for addr in eni.get("PrivateIpAddresses", [])
                            ],
                            "status": eni.get("Status"),
                            "description": eni.get("Description"),
                            "mac_address": eni.get("MacAddress"),
                        })

                normalized_func = {
                    "id": func.get("FunctionArn"),
                    "function_name": function_name,
                    "function_arn": func.get("FunctionArn"),
                    "runtime": func.get("Runtime"),
                    "role": func.get("Role"),
                    "handler": func.get("Handler"),
                    "code_size": func.get("CodeSize"),
                    "description": func.get("Description"),
                    "timeout": func.get("Timeout"),
                    "memory_size": func.get("MemorySize"),
                    "last_modified": func.get("LastModified"),
                    "code_sha256": func.get("CodeSha256"),
                    "version": func.get("Version"),
                    "state": func.get("State"),
                    "state_reason": func.get("StateReason"),
                    "state_reason_code": func.get("StateReasonCode"),
                    "last_update_status": func.get("LastUpdateStatus"),
                    # VPC Configuration
                    "vpc_id": vpc_config.get("VpcId"),
                    "subnet_ids": vpc_config.get("SubnetIds", []),
                    "security_group_ids": vpc_config.get("SecurityGroupIds", []),
                    "vpc_config_id": vpc_config.get("VpcConfigId"),
                    # ENI information
                    "network_interfaces": associated_enis,
                    "eni_count": len(associated_enis),
                    # Environment and layers
                    "environment_variables": environment.get("Variables", {}),
                    "layers": [
                        {
                            "arn": layer.get("Arn"),
                            "code_size": layer.get("CodeSize"),
                        }
                        for layer in func.get("Layers", [])
                    ],
                    # Architecture and package
                    "architectures": func.get("Architectures", []),
                    "package_type": func.get("PackageType"),
                    "image_config": func.get("ImageConfig"),
                    # Ephemeral storage
                    "ephemeral_storage": func.get("EphemeralStorage", {}).get("Size"),
                    # Signing
                    "signing_profile_version_arn": func.get("SigningProfileVersionArn"),
                    "signing_job_arn": func.get("SigningJobArn"),
                    # Metadata
                    "region": self.region,
                    "resource_type": self.resource_type.value,
                    # Enhanced metadata for enterprise analysis
                    "has_vpc_access": True,  # All functions in this list have VPC access
                    "subnet_count": len(vpc_config.get("SubnetIds", [])),
                    "security_group_count": len(vpc_config.get("SecurityGroupIds", [])),
                    "is_container_image": func.get("PackageType") == "Image",
                    "is_multi_az": len(vpc_config.get("SubnetIds", [])) > 1,
                    "layer_count": len(func.get("Layers", [])),
                    "raw": func,
                }
                normalized_functions.append(normalized_func)

            lambda_enis = normalized_functions

        logger.info(
            f"Collected {len(lambda_enis)} Lambda functions with VPC configuration in {self.region}",
            extra={
                "count": len(lambda_enis),
                "region": self.region,
                "vpc_filter": self.vpc_id,
            },
        )

        return lambda_enis
