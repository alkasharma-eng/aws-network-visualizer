"""
D3.js-based interactive HTML visualizer.
"""

import json
import time
from pathlib import Path
from typing import Optional

from src.core.config import get_settings
from src.core.constants import ResourceType
from src.core.exceptions import VisualizationException
from src.core.logging import get_logger
from src.graph.builder import GraphBuilder, NetworkGraph
from src.observability.metrics import get_metrics_publisher
from src.visualizers.base_visualizer import BaseVisualizer

logger = get_logger(__name__)


class D3Visualizer(BaseVisualizer):
    """
    Interactive HTML visualizer using D3.js force-directed graph.
    """

    def __init__(self, network_graph: NetworkGraph):
        """Initialize D3 visualizer."""
        super().__init__(network_graph)
        self.settings = get_settings()
        self.metrics = get_metrics_publisher()
        self.builder = GraphBuilder()

    def render(
        self,
        output_path: Path,
        width: Optional[int] = None,
        height: Optional[int] = None,
        **kwargs,
    ) -> Path:
        """
        Render interactive HTML visualization.

        Args:
            output_path: Output HTML file path
            width: Visualization width in pixels
            height: Visualization height in pixels
            **kwargs: Additional options

        Returns:
            Path to rendered HTML file

        Raises:
            VisualizationException: If rendering fails
        """
        start_time = time.time()

        try:
            logger.info("Rendering interactive D3.js visualization")

            # Export graph to JSON format for D3
            graph_data = self.builder.export_to_dict(self.network_graph)

            # Prepare D3 data format
            d3_data = self._prepare_d3_data(graph_data)

            # Generate HTML
            html = self._generate_html(d3_data, width, height)

            # Write to file
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)

            duration = time.time() - start_time
            logger.info(
                f"Interactive visualization saved to {output_path}",
                extra={"output_path": str(output_path), "duration": duration},
            )

            return output_path

        except Exception as e:
            logger.error(f"Failed to render D3 visualization: {e}", exc_info=True)
            raise VisualizationException(
                f"Failed to render D3 visualization: {e}",
                visualization_type="html",
            )

    def _prepare_d3_data(self, graph_data: dict) -> dict:
        """
        Prepare graph data for D3.js format.

        Args:
            graph_data: Graph data from builder

        Returns:
            D3-compatible data structure
        """
        # D3 expects nodes and links (edges)
        nodes = []
        for node in graph_data["nodes"]:
            nodes.append(
                {
                    "id": node["id"],
                    "name": node.get("name", node["id"]),
                    "type": node.get("resource_type", "unknown"),
                    "region": node.get("region"),
                    "cidr_block": node.get("cidr_block"),
                    "state": node.get("state"),
                }
            )

        links = []
        for edge in graph_data["edges"]:
            links.append(
                {
                    "source": edge["source"],
                    "target": edge["target"],
                    "relationship": edge.get("relationship", "unknown"),
                }
            )

        return {
            "nodes": nodes,
            "links": links,
            "metadata": graph_data.get("metadata", {}),
        }

    def _generate_html(
        self,
        data: dict,
        width: Optional[int],
        height: Optional[int],
    ) -> str:
        """
        Generate HTML with embedded D3.js visualization.

        Args:
            data: D3-formatted graph data
            width: Visualization width
            height: Visualization height

        Returns:
            HTML string
        """
        width = width or self.settings.visualization_width
        height = height or self.settings.visualization_height

        # Color scheme
        color_map = {
            ResourceType.VPC.value: "#3498db",
            ResourceType.SUBNET.value: "#2ecc71",
            ResourceType.EC2_INSTANCE.value: "#e74c3c",
            ResourceType.INTERNET_GATEWAY.value: "#f39c12",
            ResourceType.SECURITY_GROUP.value: "#9b59b6",
        }

        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AWS Network Topology - Interactive Visualization</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
        }}

        #container {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 20px;
        }}

        h1 {{
            margin: 0 0 20px 0;
            color: #2c3e50;
            font-size: 24px;
        }}

        #graph {{
            border: 1px solid #e1e8ed;
            border-radius: 4px;
        }}

        .node {{
            cursor: pointer;
            stroke: #fff;
            stroke-width: 2px;
        }}

        .link {{
            stroke: #999;
            stroke-opacity: 0.6;
            stroke-width: 1.5px;
        }}

        .node-label {{
            font-size: 10px;
            pointer-events: none;
            fill: #2c3e50;
            text-anchor: middle;
        }}

        .tooltip {{
            position: absolute;
            padding: 10px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            border-radius: 4px;
            pointer-events: none;
            opacity: 0;
            font-size: 12px;
            transition: opacity 0.2s;
        }}

        #legend {{
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 4px;
        }}

        .legend-item {{
            display: inline-block;
            margin-right: 20px;
            font-size: 14px;
        }}

        .legend-color {{
            display: inline-block;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            margin-right: 5px;
            vertical-align: middle;
        }}

        #controls {{
            margin-bottom: 15px;
        }}

        button {{
            padding: 8px 16px;
            margin-right: 10px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }}

        button:hover {{
            background: #2980b9;
        }}
    </style>
</head>
<body>
    <div id="container">
        <h1>AWS Network Topology - Interactive Visualization</h1>

        <div id="controls">
            <button onclick="zoomIn()">Zoom In</button>
            <button onclick="zoomOut()">Zoom Out</button>
            <button onclick="resetZoom()">Reset</button>
        </div>

        <svg id="graph" width="{width}" height="{height}"></svg>

        <div id="legend">
            <span class="legend-item">
                <span class="legend-color" style="background: {color_map[ResourceType.VPC.value]}"></span>
                VPC
            </span>
            <span class="legend-item">
                <span class="legend-color" style="background: {color_map[ResourceType.SUBNET.value]}"></span>
                Subnet
            </span>
            <span class="legend-item">
                <span class="legend-color" style="background: {color_map[ResourceType.EC2_INSTANCE.value]}"></span>
                EC2 Instance
            </span>
            <span class="legend-item">
                <span class="legend-color" style="background: {color_map[ResourceType.INTERNET_GATEWAY.value]}"></span>
                Internet Gateway
            </span>
            <span class="legend-item">
                <span class="legend-color" style="background: {color_map[ResourceType.SECURITY_GROUP.value]}"></span>
                Security Group
            </span>
        </div>

        <div class="tooltip" id="tooltip"></div>
    </div>

    <script>
        // Graph data
        const graphData = {json.dumps(data, indent=2)};

        // Color mapping
        const colorMap = {json.dumps(color_map)};

        // SVG setup
        const svg = d3.select("#graph");
        const width = {width};
        const height = {height};

        // Create zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on("zoom", (event) => {{
                g.attr("transform", event.transform);
            }});

        svg.call(zoom);

        const g = svg.append("g");

        // Create force simulation
        const simulation = d3.forceSimulation(graphData.nodes)
            .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-400))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(40));

        // Create links
        const link = g.append("g")
            .selectAll("line")
            .data(graphData.links)
            .enter()
            .append("line")
            .attr("class", "link")
            .attr("marker-end", "url(#arrowhead)");

        // Add arrowhead marker
        svg.append("defs").append("marker")
            .attr("id", "arrowhead")
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 25)
            .attr("refY", 0)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M0,-5L10,0L0,5")
            .attr("fill", "#999");

        // Create nodes
        const node = g.append("g")
            .selectAll("circle")
            .data(graphData.nodes)
            .enter()
            .append("circle")
            .attr("class", "node")
            .attr("r", 15)
            .attr("fill", d => colorMap[d.type] || "#95a5a6")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended))
            .on("mouseover", showTooltip)
            .on("mouseout", hideTooltip);

        // Add labels
        const label = g.append("g")
            .selectAll("text")
            .data(graphData.nodes)
            .enter()
            .append("text")
            .attr("class", "node-label")
            .attr("dy", 25)
            .text(d => d.name);

        // Update positions on tick
        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);

            label
                .attr("x", d => d.x)
                .attr("y", d => d.y);
        }});

        // Drag functions
        function dragstarted(event) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }}

        function dragged(event) {{
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }}

        function dragended(event) {{
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }}

        // Tooltip functions
        function showTooltip(event, d) {{
            const tooltip = d3.select("#tooltip");
            let content = `<strong>${{d.name}}</strong><br>`;
            content += `Type: ${{d.type}}<br>`;
            if (d.region) content += `Region: ${{d.region}}<br>`;
            if (d.cidr_block) content += `CIDR: ${{d.cidr_block}}<br>`;
            if (d.state) content += `State: ${{d.state}}`;

            tooltip
                .html(content)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 10) + "px")
                .style("opacity", 1);
        }}

        function hideTooltip() {{
            d3.select("#tooltip").style("opacity", 0);
        }}

        // Zoom controls
        function zoomIn() {{
            svg.transition().call(zoom.scaleBy, 1.3);
        }}

        function zoomOut() {{
            svg.transition().call(zoom.scaleBy, 0.7);
        }}

        function resetZoom() {{
            svg.transition().call(zoom.transform, d3.zoomIdentity);
        }}
    </script>
</body>
</html>
"""
        return html_template

    def get_format(self) -> str:
        """Get output format."""
        return "html"
