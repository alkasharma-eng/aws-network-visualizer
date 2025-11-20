"""
Pytest configuration and fixtures.
"""

import pytest
import boto3
from moto import mock_ec2, mock_dynamodb, mock_s3
from src.core.config import Settings


@pytest.fixture
def mock_aws():
    """Mock AWS services."""
    with mock_ec2(), mock_dynamodb(), mock_s3():
        yield


@pytest.fixture
def test_settings():
    """Test settings configuration."""
    return Settings(
        aws_region="us-east-1",
        aws_profile=None,
        enable_xray=False,
        enable_metrics=False,
        enable_ai_analysis=False,
        debug=True,
    )


@pytest.fixture
def mock_vpc_data():
    """Sample VPC data for testing."""
    return {
        "VpcId": "vpc-test123",
        "CidrBlock": "10.0.0.0/16",
        "State": "available",
        "IsDefault": False,
        "DhcpOptionsId": "dopt-123",
        "InstanceTenancy": "default",
        "Tags": [{"Key": "Name", "Value": "TestVPC"}],
    }


@pytest.fixture
def mock_subnet_data():
    """Sample subnet data for testing."""
    return {
        "SubnetId": "subnet-test456",
        "VpcId": "vpc-test123",
        "CidrBlock": "10.0.1.0/24",
        "AvailabilityZone": "us-east-1a",
        "State": "available",
        "MapPublicIpOnLaunch": False,
        "Tags": [{"Key": "Name", "Value": "TestSubnet"}],
    }


@pytest.fixture
def mock_instance_data():
    """Sample EC2 instance data for testing."""
    return {
        "InstanceId": "i-test789",
        "InstanceType": "t2.micro",
        "State": {"Name": "running"},
        "VpcId": "vpc-test123",
        "SubnetId": "subnet-test456",
        "PrivateIpAddress": "10.0.1.10",
        "Placement": {"AvailabilityZone": "us-east-1a"},
        "SecurityGroups": [{"GroupId": "sg-test", "GroupName": "default"}],
        "NetworkInterfaces": [],
        "Tags": [{"Key": "Name", "Value": "TestInstance"}],
    }
