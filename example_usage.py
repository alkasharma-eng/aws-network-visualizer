"""
Example usage of AWS Network Visualizer.

This script demonstrates how to use the AWS Network Visualizer programmatically
to discover network topology, analyze it, and detect anomalies.
"""

import asyncio
import json
from pathlib import Path

from rich.console import Console
from rich.table import Table

from src.collectors.collector_manager import CollectorManager
from src.graph.builder import GraphBuilder
from src.graph.analyzer import GraphAnalyzer
from src.ai_analysis.anomaly_detector import AnomalyDetector
from src.core.logging import setup_logging, get_logger

# Initialize console for pretty output
console = Console()

# Set up logging
setup_logging(log_level="INFO")
logger = get_logger(__name__)


async def main():
    """Main example function."""
    console.print("[bold blue]AWS Network Visualizer - Example Usage[/bold blue]\n")

    # Step 1: Discover network resources
    console.print("[bold]Step 1: Discovering AWS network resources...[/bold]")

    manager = CollectorManager(
        regions=["us-east-1"],  # Add your regions here
        profile="default",  # Or your AWS profile name
        max_concurrent=10,
    )

    try:
        # Run discovery across all regions
        results = await manager.collect_all()

        # Display summary
        summary = manager.get_summary(results)

        console.print(f"\n[green]Discovery completed successfully![/green]")
        console.print(f"Total resources discovered: {summary['total_resources']}")
        console.print(f"Regions scanned: {summary['total_regions']}\n")

        # Show resources by type
        table = Table(title="Resources by Type")
        table.add_column("Resource Type", style="cyan")
        table.add_column("Count", style="green", justify="right")

        for resource_type, count in summary["resources_by_type"].items():
            table.add_row(resource_type, str(count))

        console.print(table)

        # Step 2: Build topology graph
        console.print("\n[bold]Step 2: Building network topology graph...[/bold]")

        builder = GraphBuilder()
        network_graph = builder.build_graph(results)

        console.print(
            f"[green]Graph built successfully![/green]"
            f"\nNodes: {network_graph.node_count}"
            f"\nEdges: {network_graph.edge_count}"
        )

        # Export graph to JSON
        output_file = Path("topology_graph.json")
        with open(output_file, "w") as f:
            graph_data = builder.export_to_dict(network_graph)
            json.dump(graph_data, f, indent=2, default=str)

        console.print(f"[green]Topology saved to {output_file}[/green]")

        # Step 3: Analyze topology
        console.print("\n[bold]Step 3: Analyzing network topology...[/bold]")

        analyzer = GraphAnalyzer(network_graph)
        analysis = analyzer.analyze()

        console.print(
            f"[green]Analysis completed![/green]"
            f"\nTotal nodes: {analysis['basic_metrics']['total_nodes']}"
            f"\nTotal edges: {analysis['basic_metrics']['total_edges']}"
            f"\nGraph density: {analysis['basic_metrics']['density']:.4f}"
        )

        # Display VPC summary
        vpc_count = len(analysis.get("vpc_analysis", {}))
        console.print(f"VPCs analyzed: {vpc_count}")

        # Display connectivity
        connectivity = analysis.get("connectivity", {})
        console.print(
            f"Connected components: {connectivity.get('component_count', 0)}"
        )

        # Display isolated resources
        isolated = analysis.get("isolated_resources", [])
        if isolated:
            console.print(
                f"[yellow]Warning: Found {len(isolated)} isolated resources[/yellow]"
            )

        # Display security issues
        security = analysis.get("security_analysis", {})
        security_issues = security.get("issues_found", 0)
        if security_issues > 0:
            console.print(
                f"[red]Security issues found: {security_issues}[/red]"
            )

        # Step 4: Detect anomalies
        console.print("\n[bold]Step 4: Detecting anomalies with AI...[/bold]")

        detector = AnomalyDetector(
            network_graph,
            analyzer,
            enable_ai=True,  # Set to False to disable Bedrock AI
        )

        anomalies = detector.detect_all_anomalies()

        console.print(
            f"[green]Anomaly detection completed![/green]"
            f"\nTotal anomalies detected: {len(anomalies)}"
        )

        # Generate and display report
        report = detector.generate_report(anomalies)

        # Display anomalies by severity
        if report["total_anomalies"] > 0:
            table = Table(title="Anomalies by Severity")
            table.add_column("Severity", style="cyan")
            table.add_column("Count", style="yellow", justify="right")

            for severity, count in report["by_severity"].items():
                if count > 0:
                    style = "red" if severity == "critical" or severity == "high" else "yellow"
                    table.add_row(f"[{style}]{severity}[/{style}]", str(count))

            console.print("\n")
            console.print(table)

            # Display sample anomalies
            console.print("\n[bold]Sample Anomalies:[/bold]")
            for i, anomaly_dict in enumerate(report["anomalies"][:5], 1):
                console.print(
                    f"\n{i}. [{anomaly_dict['severity'].upper()}] {anomaly_dict['title']}"
                )
                console.print(f"   Description: {anomaly_dict['description']}")
                if anomaly_dict.get("remediation"):
                    console.print(f"   Remediation: {anomaly_dict['remediation']}")

        # Save full report
        report_file = Path("anomaly_report.json")
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        console.print(f"\n[green]Full report saved to {report_file}[/green]")

        console.print("\n[bold green]Analysis complete![/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        logger.exception("Error during execution")
        raise


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
