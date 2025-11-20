"""
Unit tests for collectors.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from src.collectors.vpc_collector import VPCCollector
from src.collectors.subnet_collector import SubnetCollector
from src.collectors.ec2_collector import EC2Collector
from src.core.constants import ResourceType


class TestVPCCollector:
    """Test VPC collector."""

    @pytest.mark.asyncio
    async def test_collect_resources(self, mock_aws, mock_vpc_data):
        """Test VPC resource collection."""
        collector = VPCCollector(region="us-east-1")

        # Mock the paginated call
        with patch.object(
            collector, "_paginated_call", return_value=[mock_vpc_data]
        ):
            resources = await collector.collect_resources()

            assert len(resources) == 1
            assert resources[0]["id"] == "vpc-test123"
            assert resources[0]["cidr_block"] == "10.0.0.0/16"
            assert resources[0]["name"] == "TestVPC"

    def test_resource_type(self):
        """Test resource type property."""
        collector = VPCCollector(region="us-east-1")
        assert collector.resource_type == ResourceType.VPC

    def test_service_name(self):
        """Test service name property."""
        collector = VPCCollector(region="us-east-1")
        assert collector.service_name == "ec2"


class TestSubnetCollector:
    """Test Subnet collector."""

    @pytest.mark.asyncio
    async def test_collect_resources(self, mock_aws, mock_subnet_data):
        """Test Subnet resource collection."""
        collector = SubnetCollector(region="us-east-1")

        with patch.object(
            collector, "_paginated_call", return_value=[mock_subnet_data]
        ):
            resources = await collector.collect_resources()

            assert len(resources) == 1
            assert resources[0]["id"] == "subnet-test456"
            assert resources[0]["vpc_id"] == "vpc-test123"
            assert resources[0]["availability_zone"] == "us-east-1a"

    @pytest.mark.asyncio
    async def test_collect_with_vpc_filter(self, mock_aws, mock_subnet_data):
        """Test collecting subnets filtered by VPC."""
        collector = SubnetCollector(region="us-east-1", vpc_id="vpc-test123")

        with patch.object(
            collector, "_paginated_call", return_value=[mock_subnet_data]
        ):
            resources = await collector.collect_resources()

            assert all(r["vpc_id"] == "vpc-test123" for r in resources)


class TestEC2Collector:
    """Test EC2 collector."""

    @pytest.mark.asyncio
    async def test_collect_resources(self, mock_aws, mock_instance_data):
        """Test EC2 instance collection."""
        collector = EC2Collector(region="us-east-1")

        # Mock the paginated call to return a reservation
        reservations = [{"Instances": [mock_instance_data]}]

        with patch.object(collector, "_paginated_call", return_value=reservations):
            resources = await collector.collect_resources()

            assert len(resources) == 1
            assert resources[0]["id"] == "i-test789"
            assert resources[0]["instance_type"] == "t2.micro"
            assert resources[0]["state"] == "running"
