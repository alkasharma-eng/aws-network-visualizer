"""
Locust load testing configuration for AWS Network Visualizer API
Usage: locust -f tests/load/locustfile.py --host=https://api.network-visualizer.com
"""

import random
import json
from locust import HttpUser, task, between, events


class NetworkVisualizerUser(HttpUser):
    """
    Simulates user behavior for the Network Visualizer API
    """
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks

    def on_start(self):
        """Called when a simulated user starts"""
        self.regions = ["us-east-1", "us-west-2", "eu-west-1"]
        self.vpc_ids = []

    @task(5)
    def get_topology_summary(self):
        """Get topology summary - most common operation"""
        with self.client.get(
            "/topology/summary",
            headers={"x-api-key": self.environment.parsed_options.api_key},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(3)
    def get_topology_for_vpc(self):
        """Get detailed topology for a specific VPC"""
        region = random.choice(self.regions)
        vpc_id = f"vpc-{random.randint(1000000, 9999999):07x}"

        with self.client.get(
            f"/topology/{region}/{vpc_id}",
            headers={"x-api-key": self.environment.parsed_options.api_key},
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:  # 404 is expected for random VPCs
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(2)
    def get_latest_anomalies(self):
        """Get latest anomaly analysis"""
        with self.client.get(
            "/analyses/latest",
            headers={"x-api-key": self.environment.parsed_options.api_key},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(1)
    def trigger_discovery(self):
        """Trigger discovery for a region (less frequent)"""
        region = random.choice(self.regions)

        with self.client.post(
            "/discovery/trigger",
            json={"regions": [region]},
            headers={"x-api-key": self.environment.parsed_options.api_key},
            catch_response=True
        ) as response:
            if response.status_code in [200, 202]:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")


class AdminUser(HttpUser):
    """
    Simulates admin user performing heavier operations
    """
    wait_time = between(5, 15)
    weight = 1  # Admin users are less common

    @task
    def trigger_full_analysis(self):
        """Trigger comprehensive analysis"""
        with self.client.post(
            "/analysis/trigger",
            json={"region": "us-east-1", "vpc_id": "vpc-12345678"},
            headers={"x-api-key": self.environment.parsed_options.api_key},
            catch_response=True
        ) as response:
            if response.status_code in [200, 202]:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")


@events.init_command_line_parser.add_listener
def _(parser):
    """Add custom command line arguments"""
    parser.add_argument(
        "--api-key",
        type=str,
        env_var="API_KEY",
        default="",
        help="API key for authentication"
    )


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the test starts"""
    print(f"Starting load test against {environment.host}")
    print(f"Users: {environment.parsed_options.num_users}")
    print(f"Spawn rate: {environment.parsed_options.spawn_rate}/s")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the test stops"""
    print("\nLoad test completed!")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Total failures: {environment.stats.total.num_failures}")
    print(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
    print(f"Requests per second: {environment.stats.total.total_rps:.2f}")
