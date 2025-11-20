"""
AI-powered analysis module using Amazon Bedrock.

This module provides intelligent analysis of network topologies using
Amazon Bedrock with Claude for anomaly detection and recommendations.
"""

from src.ai_analysis.bedrock_client import BedrockClient
from src.ai_analysis.anomaly_detector import AnomalyDetector, Anomaly

__all__ = ["BedrockClient", "AnomalyDetector", "Anomaly"]
