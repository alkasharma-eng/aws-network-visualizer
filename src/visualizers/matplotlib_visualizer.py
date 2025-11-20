"""
Matplotlib-based visualizer for PNG and SVG output.
"""

import time
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import networkx as nx

from src.core.config import get_settings
from src.core.constants import ResourceType
from src.core.exceptions import VisualizationException
from src.core.logging import get_logger
from src.graph.builder import NetworkGraph
from src.observability.metrics import get_metrics_publisher, MetricsTimer
from src.visualizers.base_visualizer import BaseVisualizer

logger = get_logger(__name__)


class MatplotlibVisualizer(BaseVisualizer):
    """
    Visualizer using Matplotlib for static images (PNG, SVG).
    """

    def __init__(self, network_graph: NetworkGraph):
        """Initialize matplotlib visualizer."""
        super().__init__(network_graph)
        self.settings = get_settings()
        self.metrics = get_metrics_publisher()

        # Color scheme for different resource types
        self.colors = {
            ResourceType.VPC.value: "#3498db",  # Blue
            ResourceType.SUBNET.value: "#2ecc71",  # Green
            ResourceType.EC2_INSTANCE.value: "#e74c3c",  # Red
            ResourceType.INTERNET_GATEWAY.value: "#f39c12",  # Orange
            ResourceType.SECURITY_GROUP.value: "#9b59b6",  # Purple
            "default": "#95a5a6",  # Gray
        }

    def render(
        self,
        output_path: Path,
        width: Optional[int] = None,
        height: Optional[int] = None,
        layout: str = "spring",
        show_labels: bool = True,
        **kwargs,
    ) -> Path:
        """
        Render network topology using Matplotlib.

        Args:
            output_path: Output file path
            width: Figure width in inches (default: 16)
            height: Figure height in inches (default: 12)
            layout: Graph layout algorithm (spring, circular, kamada_kawai)
            show_labels: Whether to show node labels
            **kwargs: Additional matplotlib options

        Returns:
            Path to rendered file

        Raises:
            VisualizationException: If rendering fails
        """
        start_time = time.time()

        try:
            logger.info(
                f"Rendering visualization with {self.graph.number_of_nodes()} nodes",
                extra={
                    "nodes": self.graph.number_of_nodes(),
                    "edges": self.graph.number_of_edges(),
                    "layout": layout,
                },
            )

            with MetricsTimer(
                self.metrics,
                "VisualizationDuration",
                {"Format": self.get_format()},
            ):
                # Create figure
                width = width or 16
                height = height or 12
                fig, ax = plt.subplots(figsize=(width, height))

                # Calculate layout
                pos = self._calculate_layout(layout)

                # Prepare node colors
                node_colors = [
                    self.colors.get(
                        self.graph.nodes[node].get("resource_type"),
                        self.colors["default"],
                    )
                    for node in self.graph.nodes()
                ]

                # Draw nodes
                nx.draw_networkx_nodes(
                    self.graph,
                    pos,
                    node_color=node_colors,
                    node_size=800,
                    alpha=0.9,
                    ax=ax,
                )

                # Draw edges
                nx.draw_networkx_edges(
                    self.graph,
                    pos,
                    edge_color="gray",
                    arrows=True,
                    arrowsize=15,
                    alpha=0.6,
                    ax=ax,
                )

                # Draw labels if requested
                if show_labels:
                    labels = self._generate_labels()
                    nx.draw_networkx_labels(
                        self.graph,
                        pos,
                        labels,
                        font_size=8,
                        font_weight="bold",
                        ax=ax,
                    )

                # Add title
                title = f"AWS Network Topology ({self.graph.number_of_nodes()} resources)"
                plt.title(title, fontsize=16, fontweight="bold")

                # Add legend
                self._add_legend(ax)

                # Remove axes
                ax.axis("off")

                # Tight layout
                plt.tight_layout()

                # Save figure
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Determine format from extension
                format = output_path.suffix[1:]  # Remove leading dot
                plt.savefig(
                    output_path,
                    format=format,
                    dpi=300 if format == "png" else None,
                    bbox_inches="tight",
                )

                plt.close(fig)

                duration = time.time() - start_time
                logger.info(
                    f"Visualization saved to {output_path}",
                    extra={"output_path": str(output_path), "duration": duration},
                )

                return output_path

        except Exception as e:
            logger.error(f"Failed to render visualization: {e}", exc_info=True)
            raise VisualizationException(
                f"Failed to render visualization: {e}",
                visualization_type=self.get_format(),
            )

    def _calculate_layout(self, layout: str) -> dict:
        """
        Calculate node positions using specified layout algorithm.

        Args:
            layout: Layout algorithm name

        Returns:
            Dictionary mapping nodes to positions
        """
        logger.debug(f"Calculating {layout} layout")

        if layout == "spring":
            return nx.spring_layout(self.graph, k=0.5, iterations=50)
        elif layout == "circular":
            return nx.circular_layout(self.graph)
        elif layout == "kamada_kawai":
            return nx.kamada_kawai_layout(self.graph)
        elif layout == "hierarchical":
            return self._hierarchical_layout()
        else:
            logger.warning(f"Unknown layout {layout}, using spring")
            return nx.spring_layout(self.graph)

    def _hierarchical_layout(self) -> dict:
        """
        Create hierarchical layout (VPCs at top, subnets below, instances at bottom).

        Returns:
            Dictionary mapping nodes to positions
        """
        pos = {}
        levels = {
            ResourceType.VPC.value: 0,
            ResourceType.INTERNET_GATEWAY.value: 0,
            ResourceType.SUBNET.value: 1,
            ResourceType.SECURITY_GROUP.value: 1,
            ResourceType.EC2_INSTANCE.value: 2,
        }

        # Group nodes by level
        nodes_by_level = {}
        for node, data in self.graph.nodes(data=True):
            resource_type = data.get("resource_type")
            level = levels.get(resource_type, 1)

            if level not in nodes_by_level:
                nodes_by_level[level] = []
            nodes_by_level[level].append(node)

        # Position nodes
        for level, nodes in nodes_by_level.items():
            y = -level  # Top to bottom
            spacing = 1.0 / (len(nodes) + 1) if nodes else 1.0

            for i, node in enumerate(nodes):
                x = (i + 1) * spacing
                pos[node] = (x, y)

        return pos

    def _generate_labels(self) -> dict:
        """
        Generate node labels.

        Returns:
            Dictionary mapping nodes to labels
        """
        labels = {}
        for node, data in self.graph.nodes(data=True):
            # Use name if available, otherwise use short ID
            name = data.get("name")
            if name:
                labels[node] = name
            else:
                # Use last part of ID (e.g., vpc-abc123 -> abc123)
                labels[node] = node.split("-")[-1] if "-" in node else node[:8]

        return labels

    def _add_legend(self, ax):
        """Add legend showing resource types."""
        from matplotlib.patches import Patch

        legend_elements = [
            Patch(
                facecolor=self.colors[ResourceType.VPC.value],
                label="VPC",
            ),
            Patch(
                facecolor=self.colors[ResourceType.SUBNET.value],
                label="Subnet",
            ),
            Patch(
                facecolor=self.colors[ResourceType.EC2_INSTANCE.value],
                label="EC2 Instance",
            ),
            Patch(
                facecolor=self.colors[ResourceType.INTERNET_GATEWAY.value],
                label="Internet Gateway",
            ),
            Patch(
                facecolor=self.colors[ResourceType.SECURITY_GROUP.value],
                label="Security Group",
            ),
        ]

        ax.legend(
            handles=legend_elements,
            loc="upper left",
            framealpha=0.9,
        )

    def get_format(self) -> str:
        """Get output format."""
        return "png"
