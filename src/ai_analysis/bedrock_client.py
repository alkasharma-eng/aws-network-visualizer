"""
Amazon Bedrock client for AI-powered analysis.

This module provides a client for interacting with Amazon Bedrock
to perform intelligent analysis of AWS network topologies.
"""

import json
import time
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError

from src.core.config import get_settings
from src.core.exceptions import AIAnalysisException
from src.core.logging import get_logger
from src.observability.metrics import get_metrics_publisher, MetricsTimer
from src.observability.tracing import trace_function

logger = get_logger(__name__)


class BedrockClient:
    """
    Client for Amazon Bedrock API with Claude models.
    """

    def __init__(self):
        """Initialize Bedrock client."""
        self.settings = get_settings()
        self.metrics = get_metrics_publisher()

        try:
            session = boto3.Session(
                profile_name=self.settings.aws_profile,
                region_name=self.settings.get_bedrock_region(),
            )
            self.client = session.client("bedrock-runtime")
            logger.info(
                f"Initialized Bedrock client with model {self.settings.bedrock_model_id}",
                extra={
                    "model_id": self.settings.bedrock_model_id,
                    "region": self.settings.get_bedrock_region(),
                },
            )
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            raise AIAnalysisException(
                f"Failed to initialize Bedrock client: {e}",
                model_id=self.settings.bedrock_model_id,
            )

    @trace_function(name="bedrock_invoke", capture_args=False)
    def invoke_model(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Invoke Bedrock model with a prompt.

        Args:
            prompt: User prompt for the model
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation (0.0 to 1.0)
            system_prompt: Optional system prompt

        Returns:
            Dictionary with model response and metadata

        Raises:
            AIAnalysisException: If model invocation fails
        """
        start_time = time.time()

        # Use config values if not provided
        if max_tokens is None:
            max_tokens = self.settings.ai_analysis_max_tokens
        if temperature is None:
            temperature = self.settings.ai_analysis_temperature

        # Build request payload for Claude 3.5
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        }

        if system_prompt:
            request_body["system"] = system_prompt

        try:
            with MetricsTimer(
                self.metrics,
                "ai_analysis_duration",
                {"Model": self.settings.bedrock_model_id},
            ):
                # Invoke model
                response = self.client.invoke_model(
                    modelId=self.settings.bedrock_model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps(request_body),
                )

                # Parse response
                response_body = json.loads(response["body"].read())

                # Extract token usage
                usage = response_body.get("usage", {})
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)

                # Record token usage metrics
                self.metrics.record_bedrock_usage(
                    model_id=self.settings.bedrock_model_id,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )

                # Extract content
                content = response_body.get("content", [])
                text_content = ""
                if content and len(content) > 0:
                    text_content = content[0].get("text", "")

                duration = time.time() - start_time

                logger.info(
                    f"Bedrock invocation successful: {input_tokens} input tokens, {output_tokens} output tokens",
                    extra={
                        "model_id": self.settings.bedrock_model_id,
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "duration": duration,
                    },
                )

                return {
                    "text": text_content,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "model_id": self.settings.bedrock_model_id,
                    "duration": duration,
                }

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error(
                f"Bedrock invocation failed: {error_code} - {e}",
                extra={
                    "model_id": self.settings.bedrock_model_id,
                    "error_code": error_code,
                },
            )

            raise AIAnalysisException(
                f"Bedrock invocation failed: {e}",
                model_id=self.settings.bedrock_model_id,
                details={"error_code": error_code},
            )

        except Exception as e:
            logger.error(
                f"Unexpected error invoking Bedrock: {e}",
                extra={"model_id": self.settings.bedrock_model_id},
                exc_info=True,
            )

            raise AIAnalysisException(
                f"Unexpected error invoking Bedrock: {e}",
                model_id=self.settings.bedrock_model_id,
            )

    def analyze_network_topology(
        self,
        topology_data: Dict[str, Any],
        analysis_type: str = "comprehensive",
    ) -> Dict[str, Any]:
        """
        Analyze network topology using Bedrock.

        Args:
            topology_data: Network topology data to analyze
            analysis_type: Type of analysis to perform

        Returns:
            Analysis results

        Raises:
            AIAnalysisException: If analysis fails
        """
        system_prompt = """You are an AWS network security and architecture expert.
Analyze the provided AWS network topology and identify security issues, misconfigurations,
cost optimization opportunities, and compliance violations.

For each finding, provide:
1. Issue type (security_misconfiguration, compliance_violation, cost_optimization, etc.)
2. Severity (critical, high, medium, low)
3. Description of the issue
4. Affected resources
5. Recommended remediation
6. Confidence score (0.0 to 1.0)

Return your analysis in JSON format with a list of findings."""

        prompt = f"""Analyze the following AWS network topology:

{json.dumps(topology_data, indent=2)}

Provide a comprehensive analysis focusing on:
1. Security group misconfigurations (especially 0.0.0.0/0 rules)
2. Network segmentation issues
3. Routing anomalies
4. Missing encryption or logging
5. Orphaned or idle resources
6. Cost optimization opportunities

Return the findings in JSON format."""

        try:
            response = self.invoke_model(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=4096,
                temperature=0.0,
            )

            # Try to parse JSON from response
            text = response["text"]
            try:
                # Extract JSON from response (may be wrapped in markdown)
                if "```json" in text:
                    json_start = text.find("```json") + 7
                    json_end = text.find("```", json_start)
                    json_text = text[json_start:json_end].strip()
                elif "```" in text:
                    json_start = text.find("```") + 3
                    json_end = text.find("```", json_start)
                    json_text = text[json_start:json_end].strip()
                else:
                    json_text = text

                findings = json.loads(json_text)

                return {
                    "findings": findings,
                    "analysis_type": analysis_type,
                    "model_response": response,
                }

            except json.JSONDecodeError as e:
                logger.warning(
                    f"Failed to parse JSON from Bedrock response: {e}",
                    extra={"response_text": text[:500]},
                )

                # Return raw text if JSON parsing fails
                return {
                    "findings": [],
                    "raw_text": text,
                    "analysis_type": analysis_type,
                    "model_response": response,
                    "parse_error": str(e),
                }

        except Exception as e:
            logger.error(f"Failed to analyze network topology: {e}", exc_info=True)
            raise AIAnalysisException(
                f"Failed to analyze network topology: {e}",
                analysis_type=analysis_type,
            )
