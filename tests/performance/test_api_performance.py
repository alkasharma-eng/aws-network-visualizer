"""
Performance tests for API endpoints
Measures response times and throughput under various conditions
"""

import pytest
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests


class TestAPIPerformance:
    """Performance tests for API endpoints"""

    @pytest.fixture(autouse=True)
    def setup(self, api_endpoint, api_key):
        """Setup test environment"""
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.headers = {"x-api-key": api_key}

    def measure_response_time(self, url, method="GET", **kwargs):
        """Measure response time for a request"""
        start = time.time()
        if method == "GET":
            response = requests.get(url, headers=self.headers, **kwargs)
        elif method == "POST":
            response = requests.post(url, headers=self.headers, **kwargs)
        end = time.time()

        return {
            "status_code": response.status_code,
            "response_time": (end - start) * 1000,  # milliseconds
            "size": len(response.content)
        }

    def test_topology_summary_response_time(self):
        """Test topology summary endpoint response time"""
        url = f"{self.api_endpoint}/topology/summary"

        # Measure 10 consecutive requests
        response_times = []
        for _ in range(10):
            result = self.measure_response_time(url)
            assert result["status_code"] == 200
            response_times.append(result["response_time"])

        avg_time = statistics.mean(response_times)
        p95_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile

        print(f"\nTopology Summary Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Min: {min(response_times):.2f}ms")
        print(f"  Max: {max(response_times):.2f}ms")
        print(f"  P95: {p95_time:.2f}ms")

        # SLA: Average < 500ms, P95 < 1000ms
        assert avg_time < 500, f"Average response time {avg_time:.2f}ms exceeds 500ms SLA"
        assert p95_time < 1000, f"P95 response time {p95_time:.2f}ms exceeds 1000ms SLA"

    def test_concurrent_requests_throughput(self):
        """Test API throughput under concurrent load"""
        url = f"{self.api_endpoint}/topology/summary"
        num_requests = 50
        concurrency = 10

        start = time.time()
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [
                executor.submit(self.measure_response_time, url)
                for _ in range(num_requests)
            ]

            results = [future.result() for future in as_completed(futures)]

        end = time.time()
        duration = end - start

        successful = sum(1 for r in results if r["status_code"] == 200)
        throughput = num_requests / duration
        avg_response_time = statistics.mean(r["response_time"] for r in results)

        print(f"\nConcurrent Requests Performance:")
        print(f"  Total requests: {num_requests}")
        print(f"  Concurrency: {concurrency}")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Successful: {successful}")
        print(f"  Throughput: {throughput:.2f} req/s")
        print(f"  Avg response time: {avg_response_time:.2f}ms")

        # SLA: 95% success rate, throughput > 20 req/s
        assert successful / num_requests >= 0.95, "Success rate below 95%"
        assert throughput > 20, f"Throughput {throughput:.2f} req/s below 20 req/s SLA"

    def test_cache_effectiveness(self):
        """Test API cache effectiveness"""
        url = f"{self.api_endpoint}/topology/summary"

        # First request (cache miss)
        first_result = self.measure_response_time(url)
        time.sleep(0.1)

        # Second request (cache hit)
        second_result = self.measure_response_time(url)

        print(f"\nCache Performance:")
        print(f"  First request (cache miss): {first_result['response_time']:.2f}ms")
        print(f"  Second request (cache hit): {second_result['response_time']:.2f}ms")
        print(f"  Improvement: {(1 - second_result['response_time'] / first_result['response_time']) * 100:.1f}%")

        # Cache should improve response time by at least 30%
        assert second_result["response_time"] < first_result["response_time"] * 0.7, \
            "Cache not improving performance by at least 30%"

    @pytest.mark.slow
    def test_sustained_load(self):
        """Test API under sustained load (5 minutes)"""
        url = f"{self.api_endpoint}/topology/summary"
        duration_seconds = 300  # 5 minutes
        target_rps = 10  # 10 requests per second

        start = time.time()
        results = []

        while time.time() - start < duration_seconds:
            batch_start = time.time()

            # Send batch of requests
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(self.measure_response_time, url)
                    for _ in range(target_rps)
                ]
                batch_results = [future.result() for future in as_completed(futures)]
                results.extend(batch_results)

            # Sleep to maintain target RPS
            elapsed = time.time() - batch_start
            sleep_time = max(0, 1.0 - elapsed)
            time.sleep(sleep_time)

        # Analyze results
        total_time = time.time() - start
        successful = sum(1 for r in results if r["status_code"] == 200)
        error_rate = (len(results) - successful) / len(results) * 100
        avg_response_time = statistics.mean(r["response_time"] for r in results)
        p95_time = statistics.quantiles([r["response_time"] for r in results], n=20)[18]
        actual_rps = len(results) / total_time

        print(f"\nSustained Load Performance:")
        print(f"  Duration: {total_time:.2f}s")
        print(f"  Total requests: {len(results)}")
        print(f"  Successful: {successful}")
        print(f"  Error rate: {error_rate:.2f}%")
        print(f"  Actual RPS: {actual_rps:.2f}")
        print(f"  Avg response time: {avg_response_time:.2f}ms")
        print(f"  P95 response time: {p95_time:.2f}ms")

        # SLA: < 1% error rate, avg < 500ms, p95 < 1000ms
        assert error_rate < 1.0, f"Error rate {error_rate:.2f}% exceeds 1% SLA"
        assert avg_response_time < 500, f"Avg response time {avg_response_time:.2f}ms exceeds 500ms SLA"
        assert p95_time < 1000, f"P95 response time {p95_time:.2f}ms exceeds 1000ms SLA"

    def test_large_payload_performance(self):
        """Test performance with large response payloads"""
        # This would test retrieving large topology graphs
        url = f"{self.api_endpoint}/topology/us-east-1/vpc-large"

        result = self.measure_response_time(url)

        print(f"\nLarge Payload Performance:")
        print(f"  Response time: {result['response_time']:.2f}ms")
        print(f"  Payload size: {result['size']} bytes ({result['size'] / 1024:.2f} KB)")

        # SLA: Response time < 3000ms even for large payloads
        assert result["response_time"] < 3000, \
            f"Large payload response time {result['response_time']:.2f}ms exceeds 3000ms SLA"


@pytest.fixture
def api_endpoint():
    """Get API endpoint from environment"""
    import os
    return os.getenv("API_ENDPOINT", "https://api.network-visualizer.com")


@pytest.fixture
def api_key():
    """Get API key from environment"""
    import os
    return os.getenv("API_KEY", "")
