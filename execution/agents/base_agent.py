#!/usr/bin/env python3
"""
Base Agent - Abstract interface for all pipeline agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path
import logging
import time


class BaseAgent(ABC):
    """
    Abstract base class for all pipeline agents.
    
    All agents must implement:
        - process(input_path, output_dir) -> dict
    
    Common functionality:
        - Configuration handling
        - Logging setup
        - Timing/metrics
        - Error handling wrapper
    """
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize agent with configuration.
        
        Args:
            config: Agent-specific configuration dict
            logger: Optional logger instance (creates one if not provided)
        """
        self.config = config
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
    
    @property
    def name(self) -> str:
        """Human-readable agent name."""
        return self.__class__.__name__
    
    @property
    def elapsed_time(self) -> float:
        """Time elapsed during last process() call."""
        if self._start_time is None:
            return 0.0
        end = self._end_time or time.time()
        return end - self._start_time
    
    @abstractmethod
    def _execute(self, input_path: Path, output_dir: Path) -> Dict[str, Any]:
        """
        Execute the agent's core logic.
        
        Subclasses must implement this method.
        
        Args:
            input_path: Path to input file
            output_dir: Directory for output files
            
        Returns:
            Dict with agent-specific results
        """
        pass
    
    def process(self, input_path: str, output_dir: str) -> Dict[str, Any]:
        """
        Process input and return results.
        
        Wraps _execute() with timing, logging, and error handling.
        
        Args:
            input_path: Path to input file
            output_dir: Directory for output files
            
        Returns:
            {
                "success": bool,
                "agent": str,
                "elapsed_time": float,
                "error": Optional[str],
                **agent_specific_results
            }
        """
        input_path = Path(input_path)
        output_dir = Path(output_dir)
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Starting {self.name}")
        self._start_time = time.time()
        
        try:
            result = self._execute(input_path, output_dir)
            self._end_time = time.time()
            
            return {
                "success": True,
                "agent": self.name,
                "elapsed_time": self.elapsed_time,
                "error": None,
                **result
            }
            
        except Exception as e:
            self._end_time = time.time()
            error_msg = f"{self.name} failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            return {
                "success": False,
                "agent": self.name,
                "elapsed_time": self.elapsed_time,
                "error": error_msg
            }
    
    def validate_input(self, input_path: Path) -> bool:
        """Check if input file exists and is readable."""
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        if not input_path.is_file():
            raise ValueError(f"Input path is not a file: {input_path}")
        return True
    
    def __repr__(self) -> str:
        return f"<{self.name}>"
