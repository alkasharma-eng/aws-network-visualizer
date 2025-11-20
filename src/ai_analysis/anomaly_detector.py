"""
Anomaly detector combining rule-based and AI-powered detection.

This module provides comprehensive anomaly detection using both
deterministic rules and AI-powered analysis.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.ai_analysis.bedrock_client import BedrockClient
from src.core.constants import AnomalyType, SeverityLevel
from src.core.logging import get_logger
from src.graph.analyzer import GraphAnalyzer
from src.graph.builder import NetworkGraph
from src.observability.metrics import get_metrics_publisher

logger = get_logger(__name__)


@dataclass
class Anomaly:
    """
    Represents a detected anomaly in the network.
    """

    anomaly_type: str
    severity: str
    title: str
    description: str
    affected_resources: List[str] = field(default_factory=list)
    remediation: Optional[str] = None
    confidence_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class AnomalyDetector:
    """
    Detects anomalies in AWS network topology using multiple methods.
    """

    def __init__(
        self,
        network_graph: NetworkGraph,
        graph_analyzer: GraphAnalyzer,
        enable_ai: bool = True,
    ):
        """
        Initialize anomaly detector.

        Args:
            network_graph: Network topology graph
            graph_analyzer: Graph analyzer instance
            enable_ai: Whether to enable AI-powered detection
        """
        self.network_graph = network_graph
        self.graph_analyzer = graph_analyzer
        self.enable_ai = enable_ai
        self.metrics = get_metrics_publisher()

        if enable_ai:
            try:
                self.bedrock_client = BedrockClient()
            except Exception as e:
                logger.warning(
                    f"Failed to initialize Bedrock client, AI detection disabled: {e}"
                )
                self.enable_ai = False
                self.bedrock_client = None
        else:
            self.bedrock_client = None

        logger.info(
            f"Initialized AnomalyDetector (AI enabled: {self.enable_ai})",
            extra={"ai_enabled": self.enable_ai},
        )

    def detect_all_anomalies(self) -> List[Anomaly]:
        """
        Detect all anomalies using both rule-based and AI methods.

        Returns:
            List of detected anomalies
        """
        start_time = time.time()
        logger.info("Starting comprehensive anomaly detection")

        anomalies = []

        # Rule-based detection
        anomalies.extend(self.detect_security_group_issues())
        anomalies.extend(self.detect_orphaned_resources())
        anomalies.extend(self.detect_network_segmentation_issues())

        # AI-powered detection
        if self.enable_ai:
            try:
                ai_anomalies = self.detect_with_ai()
                anomalies.extend(ai_anomalies)
            except Exception as e:
                logger.error(f"AI-powered detection failed: {e}", exc_info=True)

        # Record metrics
        duration = time.time() - start_time
        for anomaly in anomalies:
            self.metrics.record_anomaly(
                anomaly_type=anomaly.anomaly_type,
                severity=anomaly.severity,
            )

        logger.info(
            f"Detected {len(anomalies)} anomalies in {duration:.2f}s",
            extra={
                "total_anomalies": len(anomalies),
                "duration": duration,
            },
        )

        return anomalies

    def detect_security_group_issues(self) -> List[Anomaly]:
        """
        Detect security group misconfigurations.

        Returns:
            List of security-related anomalies
        """
        anomalies = []

        security_analysis = self.graph_analyzer.analyze_security_posture()
        issues = security_analysis.get("issues", [])

        for issue in issues:
            if issue.get("issue_type") == "overly_permissive_ingress":
                anomaly = Anomaly(
                    anomaly_type=AnomalyType.SECURITY_GROUP_MISCONFIGURATION.value,
                    severity=SeverityLevel.HIGH.value,
                    title=f"Overly permissive ingress rule in {issue.get('security_group_name')}",
                    description=issue.get("description", ""),
                    affected_resources=[issue.get("security_group_id")],
                    remediation="Restrict ingress rules to specific IP ranges or security groups instead of 0.0.0.0/0",
                    confidence_score=1.0,
                    metadata={
                        "protocol": issue.get("protocol"),
                        "from_port": issue.get("from_port"),
                        "to_port": issue.get("to_port"),
                    },
                )
                anomalies.append(anomaly)

        return anomalies

    def detect_orphaned_resources(self) -> List[Anomaly]:
        """
        Detect orphaned or isolated resources.

        Returns:
            List of orphaned resource anomalies
        """
        anomalies = []

        isolated = self.graph_analyzer.find_isolated_resources()

        for resource in isolated:
            anomaly = Anomaly(
                anomaly_type=AnomalyType.ORPHANED_RESOURCE.value,
                severity=SeverityLevel.MEDIUM.value,
                title=f"Orphaned {resource.get('resource_type')}: {resource.get('name') or resource.get('id')}",
                description=f"Resource has no connections to other resources in the topology",
                affected_resources=[resource.get("id")],
                remediation="Review if this resource is still needed and either connect it appropriately or delete it",
                confidence_score=1.0,
                metadata={
                    "resource_type": resource.get("resource_type"),
                    "region": resource.get("region"),
                },
            )
            anomalies.append(anomaly)

        return anomalies

    def detect_network_segmentation_issues(self) -> List[Anomaly]:
        """
        Detect network segmentation problems.

        Returns:
            List of segmentation anomalies
        """
        anomalies = []

        vpc_analysis = self.graph_analyzer.analyze_vpcs()

        for vpc_id, vpc_data in vpc_analysis.items():
            # Check if VPC has no subnets
            if vpc_data.get("subnet_count", 0) == 0:
                anomaly = Anomaly(
                    anomaly_type=AnomalyType.NETWORK_SEGMENTATION_VIOLATION.value,
                    severity=SeverityLevel.MEDIUM.value,
                    title=f"VPC {vpc_data.get('name') or vpc_id} has no subnets",
                    description="VPC exists without any subnets, which may indicate incomplete setup",
                    affected_resources=[vpc_id],
                    remediation="Create subnets for this VPC or remove it if not needed",
                    confidence_score=1.0,
                    metadata={"region": vpc_data.get("region")},
                )
                anomalies.append(anomaly)

            # Check if VPC has no internet connectivity
            if (
                vpc_data.get("instance_count", 0) > 0
                and not vpc_data.get("has_internet_connectivity")
            ):
                anomaly = Anomaly(
                    anomaly_type=AnomalyType.ROUTING_ANOMALY.value,
                    severity=SeverityLevel.LOW.value,
                    title=f"VPC {vpc_data.get('name') or vpc_id} has instances but no Internet Gateway",
                    description=f"VPC has {vpc_data.get('instance_count')} instances but no Internet Gateway attached",
                    affected_resources=[vpc_id],
                    remediation="Attach an Internet Gateway if instances need internet access, or verify NAT Gateway configuration",
                    confidence_score=0.7,
                    metadata={
                        "instance_count": vpc_data.get("instance_count"),
                        "region": vpc_data.get("region"),
                    },
                )
                anomalies.append(anomaly)

        return anomalies

    def detect_with_ai(self) -> List[Anomaly]:
        """
        Use Bedrock AI to detect complex anomalies.

        Returns:
            List of AI-detected anomalies
        """
        if not self.enable_ai or not self.bedrock_client:
            return []

        logger.info("Starting AI-powered anomaly detection")

        try:
            # Prepare topology data for analysis
            topology_data = {
                "graph_summary": self.graph_analyzer.get_basic_metrics(),
                "vpcs": self.graph_analyzer.analyze_vpcs(),
                "security_posture": self.graph_analyzer.analyze_security_posture(),
                "connectivity": self.graph_analyzer.analyze_connectivity(),
            }

            # Invoke Bedrock for analysis
            analysis_result = self.bedrock_client.analyze_network_topology(
                topology_data=topology_data,
                analysis_type="comprehensive",
            )

            # Convert AI findings to Anomaly objects
            anomalies = []
            findings = analysis_result.get("findings", [])

            if isinstance(findings, dict) and "findings" in findings:
                findings = findings["findings"]

            for finding in findings:
                if not isinstance(finding, dict):
                    continue

                anomaly = Anomaly(
                    anomaly_type=finding.get(
                        "type", AnomalyType.COMPLIANCE_VIOLATION.value
                    ),
                    severity=finding.get("severity", SeverityLevel.MEDIUM.value),
                    title=finding.get("title", "AI-detected issue"),
                    description=finding.get("description", ""),
                    affected_resources=finding.get("affected_resources", []),
                    remediation=finding.get("remediation"),
                    confidence_score=finding.get("confidence_score", 0.8),
                    metadata={
                        "source": "bedrock_ai",
                        "model_id": analysis_result.get("model_response", {}).get(
                            "model_id"
                        ),
                    },
                )
                anomalies.append(anomaly)

            logger.info(
                f"AI detection found {len(anomalies)} anomalies",
                extra={"ai_anomalies": len(anomalies)},
            )

            return anomalies

        except Exception as e:
            logger.error(f"AI-powered detection failed: {e}", exc_info=True)
            return []

    def generate_report(self, anomalies: List[Anomaly]) -> Dict[str, Any]:
        """
        Generate a comprehensive anomaly report.

        Args:
            anomalies: List of detected anomalies

        Returns:
            Report dictionary
        """
        # Group by severity
        by_severity = {
            SeverityLevel.CRITICAL.value: [],
            SeverityLevel.HIGH.value: [],
            SeverityLevel.MEDIUM.value: [],
            SeverityLevel.LOW.value: [],
            SeverityLevel.INFO.value: [],
        }

        for anomaly in anomalies:
            severity = anomaly.severity
            if severity in by_severity:
                by_severity[severity].append(anomaly)

        # Group by type
        by_type = {}
        for anomaly in anomalies:
            anomaly_type = anomaly.anomaly_type
            if anomaly_type not in by_type:
                by_type[anomaly_type] = []
            by_type[anomaly_type].append(anomaly)

        return {
            "total_anomalies": len(anomalies),
            "by_severity": {
                severity: len(items) for severity, items in by_severity.items()
            },
            "by_type": {atype: len(items) for atype, items in by_type.items()},
            "anomalies": [
                {
                    "type": a.anomaly_type,
                    "severity": a.severity,
                    "title": a.title,
                    "description": a.description,
                    "affected_resources": a.affected_resources,
                    "remediation": a.remediation,
                    "confidence_score": a.confidence_score,
                }
                for a in anomalies
            ],
        }
