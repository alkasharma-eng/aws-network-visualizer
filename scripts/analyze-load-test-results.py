#!/usr/bin/env python3
"""
Analyze load test results and check against SLAs
"""

import sys
import json
import csv
from pathlib import Path


class LoadTestAnalyzer:
    """Analyzes load test results and checks SLA compliance"""

    def __init__(self, results_dir):
        self.results_dir = Path(results_dir)
        self.slas = {
            "error_rate": 1.0,  # < 1%
            "avg_response_time": 500,  # < 500ms
            "p95_response_time": 1000,  # < 1000ms
            "p99_response_time": 2000,  # < 2000ms
            "throughput": 20,  # > 20 req/s
        }

    def analyze_locust_results(self):
        """Analyze Locust CSV results"""
        print("\n=== Locust Results Analysis ===")

        stats_file = self.results_dir / "locust_stats.csv"
        if not stats_file.exists():
            print("  No Locust stats file found")
            return None

        with open(stats_file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["Type"] == "Aggregated":
                    error_rate = float(row["Failure Count"]) / float(row["Request Count"]) * 100 if float(row["Request Count"]) > 0 else 0
                    avg_response = float(row["Average Response Time"])
                    p95_response = float(row["95%"])
                    throughput = float(row["Requests/s"])

                    print(f"  Error Rate: {error_rate:.2f}% (SLA: < {self.slas['error_rate']}%)")
                    print(f"  Avg Response Time: {avg_response:.2f}ms (SLA: < {self.slas['avg_response_time']}ms)")
                    print(f"  P95 Response Time: {p95_response:.2f}ms (SLA: < {self.slas['p95_response_time']}ms)")
                    print(f"  Throughput: {throughput:.2f} req/s (SLA: > {self.slas['throughput']} req/s)")

                    violations = []
                    if error_rate >= self.slas["error_rate"]:
                        violations.append("Error Rate")
                    if avg_response >= self.slas["avg_response_time"]:
                        violations.append("Avg Response Time")
                    if p95_response >= self.slas["p95_response_time"]:
                        violations.append("P95 Response Time")
                    if throughput <= self.slas["throughput"]:
                        violations.append("Throughput")

                    if violations:
                        print(f"\n  ❌ SLA Violations: {', '.join(violations)}")
                        return False
                    else:
                        print("\n  ✅ All SLAs met")
                        return True

        return None

    def analyze_artillery_results(self):
        """Analyze Artillery JSON results"""
        print("\n=== Artillery Results Analysis ===")

        results_file = self.results_dir / "artillery-results.json"
        if not results_file.exists():
            print("  No Artillery results file found")
            return None

        with open(results_file) as f:
            data = json.load(f)

        aggregate = data.get("aggregate", {})
        latency = aggregate.get("latency", {})
        counters = aggregate.get("counters", {})

        total_requests = counters.get("http.requests", 0)
        failed_requests = counters.get("http.request_failed", 0)
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0

        median = latency.get("median", 0)
        p95 = latency.get("p95", 0)
        p99 = latency.get("p99", 0)

        print(f"  Total Requests: {total_requests}")
        print(f"  Failed Requests: {failed_requests}")
        print(f"  Error Rate: {error_rate:.2f}% (SLA: < {self.slas['error_rate']}%)")
        print(f"  Median Response Time: {median:.2f}ms")
        print(f"  P95 Response Time: {p95:.2f}ms (SLA: < {self.slas['p95_response_time']}ms)")
        print(f"  P99 Response Time: {p99:.2f}ms (SLA: < {self.slas['p99_response_time']}ms)")

        violations = []
        if error_rate >= self.slas["error_rate"]:
            violations.append("Error Rate")
        if p95 >= self.slas["p95_response_time"]:
            violations.append("P95 Response Time")
        if p99 >= self.slas["p99_response_time"]:
            violations.append("P99 Response Time")

        if violations:
            print(f"\n  ❌ SLA Violations: {', '.join(violations)}")
            return False
        else:
            print("\n  ✅ All SLAs met")
            return True

    def generate_summary(self):
        """Generate summary report"""
        print("\n" + "="*50)
        print("LOAD TEST SUMMARY")
        print("="*50)

        locust_passed = self.analyze_locust_results()
        artillery_passed = self.analyze_artillery_results()

        all_passed = True
        if locust_passed is not None:
            all_passed = all_passed and locust_passed
        if artillery_passed is not None:
            all_passed = all_passed and artillery_passed

        print("\n" + "="*50)
        if all_passed:
            print("✅ ALL LOAD TESTS PASSED")
            print("="*50)
            return 0
        else:
            print("❌ SOME LOAD TESTS FAILED")
            print("="*50)
            return 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze-load-test-results.py <results_dir>")
        sys.exit(1)

    analyzer = LoadTestAnalyzer(sys.argv[1])
    exit_code = analyzer.generate_summary()
    sys.exit(exit_code)
