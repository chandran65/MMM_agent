"""
State Manager

Manages pipeline state persistence and recovery.
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Any
import logging


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy types."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        return super(NumpyEncoder, self).default(obj)


class StateManager:
    """Manage pipeline execution state."""
    
    def __init__(self, config: Dict):
        """
        Initialize state manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # State file path
        self.state_file = Path(
            config['orchestration'].get('state_file', 'orchestration/pipeline_state.json')
        )
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
    
    def save_stage_output(self, stage_name: str, output: Dict) -> None:
        """
        Save output from a single stage.
        
        Args:
            stage_name: Name of the stage
            output: Stage output dictionary
        """
        # Load existing state
        state = self.load_state()
        
        # Initialize state if None or ensure stages key exists
        if state is None:
            state = {"stages": {}}
        elif "stages" not in state:
            state["stages"] = {}
        
        # Update with new stage
        state["stages"][stage_name] = {
            "output": output,
            "timestamp": self._get_timestamp(),
            "status": output.get("status", "unknown")
        }
        
        # Save back to file with custom encoder
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2, cls=NumpyEncoder)
        
        self.logger.info(f"Saved state for stage: {stage_name}")
    
    def save_pipeline_state(self, pipeline_result: Dict) -> None:
        """
        Save complete pipeline state.
        
        Args:
            pipeline_result: Complete pipeline result dictionary
        """
        state = {
            "pipeline_result": pipeline_result,
            "timestamp": self._get_timestamp()
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2, cls=NumpyEncoder)
        
        self.logger.info(f"Saved complete pipeline state to {self.state_file}")
    
    def load_state(self) -> Optional[Dict]:
        """
        Load saved state.
        
        Returns:
            Saved state dictionary or None if no state exists
        """
        if not self.state_file.exists():
            return None
        
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            self.logger.warning("Failed to load state file - corrupted JSON")
            return None
    
    def get_stage_output(self, stage_name: str) -> Optional[Dict]:
        """
        Get output for a specific stage.
        
        Args:
            stage_name: Name of the stage
            
        Returns:
            Stage output dictionary or None
        """
        state = self.load_state()
        
        if not state:
            return None
        
        return state.get("stages", {}).get(stage_name, {}).get("output")
    
    def clear_state(self) -> None:
        """Clear all saved state."""
        if self.state_file.exists():
            self.state_file.unlink()
            self.logger.info("Cleared pipeline state")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as ISO format string."""
        from datetime import datetime
        return datetime.now().isoformat()
