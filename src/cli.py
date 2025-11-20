"""
Command-line interface for AWS Network Visualizer.

This module provides a comprehensive CLI for network topology discovery,
analysis, visualization, and anomaly detection.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.ai_analysis.anomaly_detector import AnomalyDetector
from src.collectors.collector_manager import CollectorManager
from src.core.config import get_settings
from src.core.logging import setup_logging, get_logger
from src.graph.analyzer import GraphAnalyzer
from src.graph.builder import GraphBuilder

console = Console()
logger = None


def init_logger(debug: bool = False):
    """Initialize logger."""
    global logger
    log_level = "DEBUG" if debug else "INFO"
    setup_logging(log_level=log_level)
    logger = get_logger(__name__)


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.option("--profile", help="AWS CLI profile to use")
@click.option("--region", help="AWS region (can specify multiple with commas)")
@click.pass_context
def cli(ctx, debug, profile, region):
    """
    AWS Network Visualizer - Production-Grade Network Topology Discovery.

    Discover, analyze, and visualize AWS network infrastructure with
    comprehensive observability and AI-powered anomaly detection.
    """
    init_logger(debug)
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug
    ctx.obj["profile"] = profile
    ctx.obj["regions"] = region.split(",") if region else None


@cli.command()
@click.option(
    "--output",
    "-o",
    default="topology.json",
    help="Output file path",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="Output format",
)
@click.pass_context
def discover(ctx, output, format):
    """
    Discover AWS network resources across all configured regions.

    This command collects VPCs, Subnets, EC2 instances, Security Groups,
    Internet Gateways, and other network resources, building a comprehensive
    topology graph.
    """
    console.print("[bold blue]Starting AWS Network Discovery...[/bold blue]")

    try:
        # Create collector manager
        manager = CollectorManager(
            regions=ctx.obj.get("regions"),
            profile=ctx.obj.get("profile"),
        )

        # Run discovery
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Discovering resources...", total=None)

            # Run async collection
            results = asyncio.run(manager.collect_all())

            progress.update(task, completed=True)

        # Generate summary
        summary = manager.get_summary(results)

        console.print("\n[bold green]Discovery Complete![/bold green]")
        console.print(f"Total Resources: {summary['total_resources']}")
        console.print(f"Regions: {summary['total_regions']}")

        # Display resource counts
        table = Table(title="Resources by Type")
        table.add_column("Resource Type", style="cyan")
        table.add_column("Count", style="green", justify="right")

        for resource_type, count in summary["resources_by_type"].items():
            table.add_row(resource_type, str(count))

        console.print(table)

        # Build graph
        console.print("\n[bold blue]Building topology graph...[/bold blue]")
        builder = GraphBuilder()
        network_graph = builder.build_graph(results)

        console.print(
            f"[green]Graph built: {network_graph.node_count} nodes, "
            f"{network_graph.edge_count} edges[/green]"
        )

        # Export results
        console.print(f"\n[bold blue]Exporting to {output}...[/bold blue]")

        topology_data = {
            "summary": summary,
            "graph": builder.export_to_dict(network_graph),
            "metadata": network_graph.metadata,
        }

        output_path = Path(output)
        with open(output_path, "w") as f:
            if format == "json":
                json.dump(topology_data, f, indent=2, default=str)
            # Add YAML support if needed

        console.print(f"[green]Topology saved to {output}[/green]")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        if ctx.obj.get("debug"):
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.argument("topology_file", type=click.Path(exists=True))
@click.option(
    "--output",
    "-o",
    default="analysis.json",
    help="Output file for analysis results",
)
@click.option(
    "--enable-ai/--no-ai",
    default=True,
    help="Enable AI-powered analysis with Bedrock",
)
@click.pass_context
def analyze(ctx, topology_file, output, enable_ai):
    """
    Analyze network topology for issues and anomalies.

    This command performs comprehensive analysis including:
    - Connectivity analysis
    - Security posture assessment
    - Orphaned resource detection
    - AI-powered anomaly detection (if enabled)
    """
    console.print("[bold blue]Analyzing network topology...[/bold blue]")

    try:
        # Load topology data
        with open(topology_file, "r") as f:
            topology_data = json.load(f)

        # Rebuild graph from data
        console.print("Rebuilding graph...")
        # Note: In production, you'd implement graph deserialization
        # For now, we'll run discovery again

        manager = CollectorManager(
            regions=ctx.obj.get("regions"),
            profile=ctx.obj.get("profile"),
        )

        results = asyncio.run(manager.collect_all())

        builder = GraphBuilder()
        network_graph = builder.build_graph(results)

        # Analyze graph
        console.print("[bold blue]Running analysis...[/bold blue]")
        analyzer = GraphAnalyzer(network_graph)
        analysis_results = analyzer.analyze()

        console.print("\n[bold green]Analysis Results:[/bold green]")

        # Display basic metrics
        metrics = analysis_results["basic_metrics"]
        console.print(f"Total Nodes: {metrics['total_nodes']}")
        console.print(f"Total Edges: {metrics['total_edges']}")
        console.print(f"Graph Density: {metrics['density']:.4f}")

        # Display security issues
        security = analysis_results.get("security_analysis", {})
        issues_count = security.get("issues_found", 0)

        if issues_count > 0:
            console.print(f"\n[bold yellow]Security Issues Found: {issues_count}[/bold yellow]")

        # Run anomaly detection
        console.print("\n[bold blue]Detecting anomalies...[/bold blue]")
        detector = AnomalyDetector(network_graph, analyzer, enable_ai=enable_ai)
        anomalies = detector.detect_all_anomalies()

        # Generate report
        report = detector.generate_report(anomalies)

        console.print(f"\n[bold]Total Anomalies: {report['total_anomalies']}[/bold]")

        # Display by severity
        table = Table(title="Anomalies by Severity")
        table.add_column("Severity", style="cyan")
        table.add_column("Count", style="yellow", justify="right")

        for severity, count in report["by_severity"].items():
            if count > 0:
                table.add_row(severity, str(count))

        console.print(table)

        # Save results
        output_path = Path(output)
        with open(output_path, "w") as f:
            combined_results = {
                "analysis": analysis_results,
                "anomaly_report": report,
            }
            json.dump(combined_results, f, indent=2, default=str)

        console.print(f"\n[green]Analysis saved to {output}[/green]")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        if ctx.obj.get("debug"):
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.argument("topology_file", type=click.Path(exists=True))
@click.option(
    "--output",
    "-o",
    default="network_visualization.png",
    help="Output visualization file",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["png", "svg", "html"]),
    default="png",
    help="Visualization format",
)
@click.option(
    "--layout",
    type=click.Choice(["spring", "circular", "kamada_kawai", "hierarchical"]),
    default="spring",
    help="Graph layout algorithm",
)
@click.option(
    "--width",
    type=int,
    help="Visualization width in pixels",
)
@click.option(
    "--height",
    type=int,
    help="Visualization height in pixels",
)
@click.pass_context
def visualize(ctx, topology_file, output, format, layout, width, height):
    """
    Generate network topology visualizations.

    Creates visual representations of the network topology in various formats.
    Supports PNG/SVG (static) and HTML (interactive D3.js).
    """
    console.print("[bold blue]Generating visualization...[/bold blue]")

    try:
        from src.visualizers.matplotlib_visualizer import MatplotlibVisualizer
        from src.visualizers.d3_visualizer import D3Visualizer

        # Load topology
        with open(topology_file, "r") as f:
            topology_data = json.load(f)

        # Rebuild graph
        console.print("Rebuilding graph from topology data...")

        # For now, we need to run discovery again
        # In production, you'd deserialize the graph
        manager = CollectorManager(
            regions=ctx.obj.get("regions"),
            profile=ctx.obj.get("profile"),
        )

        results = asyncio.run(manager.collect_all())
        builder = GraphBuilder()
        network_graph = builder.build_graph(results)

        # Generate visualization
        console.print(f"Rendering {format.upper()} visualization...")

        output_path = Path(output)

        if format in ["png", "svg"]:
            visualizer = MatplotlibVisualizer(network_graph)
            # Ensure output has correct extension
            if not output_path.suffix:
                output_path = output_path.with_suffix(f".{format}")
            visualizer.render(
                output_path,
                width=width,
                height=height,
                layout=layout,
            )
        elif format == "html":
            visualizer = D3Visualizer(network_graph)
            if not output_path.suffix:
                output_path = output_path.with_suffix(".html")
            visualizer.render(
                output_path,
                width=width,
                height=height,
            )

        console.print(f"[green]Visualization saved to {output_path}[/green]")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        if ctx.obj.get("debug"):
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.pass_context
def info(ctx):
    """Display configuration and system information."""
    settings = get_settings()

    console.print("[bold blue]AWS Network Visualizer Configuration[/bold blue]\n")

    table = Table(show_header=False)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Version", settings.app_version)
    table.add_row("Environment", settings.environment)
    table.add_row("AWS Region", settings.aws_region)
    table.add_row("AWS Profile", settings.aws_profile or "default")
    table.add_row("Log Level", settings.log_level)
    table.add_row("X-Ray Enabled", str(settings.enable_xray))
    table.add_row("Metrics Enabled", str(settings.enable_metrics))
    table.add_row("AI Analysis", str(settings.enable_ai_analysis))
    table.add_row("Bedrock Model", settings.bedrock_model_id)

    console.print(table)


def main():
    """Main entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
