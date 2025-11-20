"""
Base visualizer class.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from src.core.logging import get_logger
from src.graph.builder import NetworkGraph

logger = get_logger(__name__)


class BaseVisualizer(ABC):
    """
    Abstract base class for network topology visualizers.
    """

    def __init__(self, network_graph: NetworkGraph):
        """
        Initialize visualizer.

        Args:
            network_graph: Network topology graph to visualize
        """
        self.network_graph = network_graph
        self.graph = network_graph.graph
        logger.info(f"Initialized {self.__class__.__name__}")

    @abstractmethod
    def render(
        self,
        output_path: Path,
        width: Optional[int] = None,
        height: Optional[int] = None,
        **kwargs,
    ) -> Path:
        """
        Render the visualization.

        Args:
            output_path: Path to save visualization
            width: Width in pixels
            height: Height in pixels
            **kwargs: Additional renderer-specific options

        Returns:
            Path to rendered file
        """
        pass

    @abstractmethod
    def get_format(self) -> str:
        """
        Get output format for this visualizer.

        Returns:
            Format string (png, svg, html, etc.)
        """
        pass
