"""
Checkpoint Manager

Manages human-in-the-loop checkpoints for pipeline approval.
"""

import json
from typing import Dict
import logging


class CheckpointManager:
    """Manage pipeline checkpoints for human approval."""
    
    def __init__(self, config: Dict):
        """
        Initialize checkpoint manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Get checkpoint configuration
        self.checkpoints_enabled = config['orchestration'].get('enable_checkpoints', True)
        self.checkpoint_locations = config['orchestration'].get('checkpoint_locations', [])
    
    def request_approval(self, checkpoint_name: str, context: Dict) -> bool:
        """
        Request human approval at a checkpoint.
        
        Args:
            checkpoint_name: Name of the checkpoint
            context: Context data to display for approval
            
        Returns:
            True if approved, False otherwise
        """
        if not self.checkpoints_enabled:
            self.logger.info(f"Checkpoints disabled - auto-approving {checkpoint_name}")
            return True
        
        if checkpoint_name not in self.checkpoint_locations:
            self.logger.info(f"Checkpoint {checkpoint_name} not in configured locations - skipping")
            return True
        
        self.logger.info("="*60)
        self.logger.info(f"CHECKPOINT: {checkpoint_name}")
        self.logger.info("="*60)
        
        # Display context
        self.logger.info("Context:")
        self.logger.info(json.dumps(context, indent=2, default=str))
        
        # Request approval
        print("\n" + "="*60)
        print(f"CHECKPOINT: {checkpoint_name}")
        print("="*60)
        print("\nReview the output above.")
        
        # In a real implementation, this could integrate with:
        # - Web UI for approval
        # - Slack/Teams notifications
        # - Approval workflows
        
        response = input("\nProceed to next stage? (yes/no): ").strip().lower()
        
        approved = response in ['yes', 'y']
        
        if approved:
            self.logger.info(f"Checkpoint {checkpoint_name} APPROVED")
        else:
            self.logger.warning(f"Checkpoint {checkpoint_name} REJECTED - stopping pipeline")
            raise ValueError(f"Pipeline stopped at checkpoint: {checkpoint_name}")
        
        return approved
    
    def save_checkpoint(self, checkpoint_name: str, data: Dict) -> None:
        """
        Save checkpoint data for later review.
        
        Args:
            checkpoint_name: Name of the checkpoint
            data: Data to save
        """
        from pathlib import Path
        
        checkpoint_dir = Path("orchestration/checkpoints")
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        checkpoint_file = checkpoint_dir / f"{checkpoint_name}.json"
        
        with open(checkpoint_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        self.logger.info(f"Saved checkpoint data to {checkpoint_file}")
