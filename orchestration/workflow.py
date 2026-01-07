"""
Workflow Orchestrator

Manages the execution flow of all MMX agents with checkpoints and state management.
"""

import yaml
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from .state_manager import StateManager
from .checkpoints import CheckpointManager

# Import all agents
import sys
sys.path.append(str(Path(__file__).parent.parent))

from agents.segmentation_agent.agent import SegmentationAgent
from agents.trend_scanner_agent.agent import TrendScannerAgent
from agents.baseline_agent.agent import BaselineAgent
from agents.model_optimization_agent.agent import ModelOptimizationAgent
from agents.budget_optimization_agent.agent import BudgetOptimizationAgent
from agents.insight_agent.agent import InsightAgent


class WorkflowOrchestrator:
    """
    Orchestrates the end-to-end MMX workflow.
    
    Responsibilities:
    - Manage agent execution order
    - Handle checkpoints for human-in-the-loop
    - Persist state between stages
    - Handle errors and retries
    - Generate workflow logs
    """
    
    def __init__(self, config_path: str = "config/global.yaml"):
        """
        Initialize the workflow orchestrator.
        
        Args:
            config_path: Path to global configuration
        """
        self.config = self._load_config(config_path)
        self.state_manager = StateManager(self.config)
        self.checkpoint_manager = CheckpointManager(self.config)
        
        # Set up logging
        self.logger = self._setup_logging()
        
        # Initialize agents (lazy loading)
        self.agents = {}
        
        # Workflow state
        self.workflow_status = "initialized"
        self.current_stage = None
        self.completed_stages = []
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _setup_logging(self) -> logging.Logger:
        """Set up workflow logging."""
        log_config = self.config['orchestration']
        log_level = getattr(logging, log_config.get('log_level', 'INFO'))
        
        # Create logs directory
        log_file = log_config.get('log_file', 'logs/mmx_pipeline.log')
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        return logging.getLogger(__name__)
    
    def execute_full_pipeline(
        self,
        input_data_path: str,
        events_path: Optional[str] = None,
        auto_approve_checkpoints: bool = False
    ) -> Dict:
        """
        Execute the complete MMX pipeline.
        
        Args:
            input_data_path: Path to input sales and spend data
            events_path: Optional path to known events data
            auto_approve_checkpoints: If True, automatically approve all checkpoints
            
        Returns:
            Dictionary with execution results
        """
        self.logger.info("="*60)
        self.logger.info("Starting MMX Pipeline Execution")
        self.logger.info("="*60)
        
        start_time = datetime.now()
        
        try:
            # Stage 1: Segmentation
            self.logger.info("\n### STAGE 1: SEGMENTATION ###")
            self.current_stage = "segmentation"
            segmentation_result = self._execute_segmentation(input_data_path)
            self.state_manager.save_stage_output("segmentation", segmentation_result)
            self.completed_stages.append("segmentation")
            
            # Checkpoint 1: After segmentation
            if not auto_approve_checkpoints:
                self.checkpoint_manager.request_approval(
                    "segmentation",
                    segmentation_result
                )
            
            # Stage 2: Trend Scanner
            self.logger.info("\n### STAGE 2: TREND SCANNER ###")
            self.current_stage = "trend_scanner"
            trend_result = self._execute_trend_scanner(input_data_path, events_path)
            self.state_manager.save_stage_output("trend_scanner", trend_result)
            self.completed_stages.append("trend_scanner")
            
            # Stage 3: Baseline Estimation
            self.logger.info("\n### STAGE 3: BASELINE ESTIMATION ###")
            self.current_stage = "baseline"
            baseline_result = self._execute_baseline(
                input_data_path,
                trend_result['output_paths']['event_metadata']
            )
            self.state_manager.save_stage_output("baseline", baseline_result)
            self.completed_stages.append("baseline")
            
            # Checkpoint 2: After baseline
            if not auto_approve_checkpoints:
                self.checkpoint_manager.request_approval(
                    "baseline",
                    baseline_result
                )
            
            # Stage 4: Model Optimization
            self.logger.info("\n### STAGE 4: MODEL OPTIMIZATION ###")
            self.current_stage = "model_optimization"
            model_result = self._execute_model_optimization(
                input_data_path,
                baseline_result['output_paths']['priors'],
                baseline_result['output_paths']['baseline_estimates']
            )
            self.state_manager.save_stage_output("model_optimization", model_result)
            self.completed_stages.append("model_optimization")
            
            # Stage 5: Budget Optimization
            self.logger.info("\n### STAGE 5: BUDGET OPTIMIZATION ###")
            self.current_stage = "budget_optimization"
            
            # Checkpoint 3: Before optimization
            if not auto_approve_checkpoints:
                self.checkpoint_manager.request_approval(
                    "before_optimization",
                    model_result
                )
            
            budget_result = self._execute_budget_optimization(
                model_result['output_paths']['response_curves'],
                input_data_path
            )
            self.state_manager.save_stage_output("budget_optimization", budget_result)
            self.completed_stages.append("budget_optimization")
            
            # Stage 6: Insight Generation
            self.logger.info("\n### STAGE 6: INSIGHT GENERATION ###")
            self.current_stage = "insight_generation"
            insight_result = self._execute_insight_generation(
                model_result['output_paths']['contributions_csv'],
                budget_result['output_paths']['recommendations'],
                model_result['output_paths']['metrics'],
                model_result['output_paths'].get('response_curves')
            )
            self.state_manager.save_stage_output("insight_generation", insight_result)
            self.completed_stages.append("insight_generation")
            
            # Pipeline complete
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.workflow_status = "completed"
            
            pipeline_result = {
                "status": "success",
                "completed_stages": self.completed_stages,
                "duration_seconds": duration,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "outputs": {
                    "segmentation": segmentation_result,
                    "trend_scanner": trend_result,
                    "baseline": baseline_result,
                    "model_optimization": model_result,
                    "budget_optimization": budget_result,
                    "insight_generation": insight_result
                }
            }
            
            # Save final pipeline state
            self.state_manager.save_pipeline_state(pipeline_result)
            
            self.logger.info("="*60)
            self.logger.info(f"Pipeline Completed Successfully in {duration:.1f} seconds")
            self.logger.info("="*60)
            
            return pipeline_result
            
        except Exception as e:
            self.logger.error(f"Pipeline failed at stage '{self.current_stage}': {str(e)}", exc_info=True)
            self.workflow_status = "failed"
            
            return {
                "status": "failed",
                "error": str(e),
                "failed_stage": self.current_stage,
                "completed_stages": self.completed_stages
            }
    
    def _execute_segmentation(self, input_data_path: str) -> Dict:
        """Execute segmentation agent."""
        agent = SegmentationAgent()
        self.agents['segmentation'] = agent
        return agent.execute(input_data_path)
    
    def _execute_trend_scanner(
        self,
        input_data_path: str,
        events_path: Optional[str]
    ) -> Dict:
        """Execute trend scanner agent."""
        agent = TrendScannerAgent()
        self.agents['trend_scanner'] = agent
        return agent.execute(input_data_path, events_path)
    
    def _execute_baseline(
        self,
        sales_data_path: str,
        event_metadata_path: str
    ) -> Dict:
        """Execute baseline agent."""
        agent = BaselineAgent()
        self.agents['baseline'] = agent
        return agent.execute(sales_data_path, event_metadata_path)
    
    def _execute_model_optimization(
        self,
        sales_data_path: str,
        priors_path: str,
        baseline_path: str
    ) -> Dict:
        """Execute model optimization agent."""
        agent = ModelOptimizationAgent()
        self.agents['model_optimization'] = agent
        return agent.execute(sales_data_path, priors_path, baseline_path)
    
    def _execute_budget_optimization(
        self,
        response_curves_path: str,
        current_spend_path: str
    ) -> Dict:
        """Execute budget optimization agent."""
        agent = BudgetOptimizationAgent()
        self.agents['budget_optimization'] = agent
        return agent.execute(response_curves_path, current_spend_path)
    
    def _execute_insight_generation(
        self,
        contributions_path: str,
        optimization_path: str,
        model_metrics_path: str,
        response_curves_path: Optional[str]
    ) -> Dict:
        """Execute insight generation agent."""
        agent = InsightAgent()
        self.agents['insight_generation'] = agent
        return agent.execute(
            contributions_path,
            optimization_path,
            model_metrics_path,
            response_curves_path
        )
    
    def resume_from_checkpoint(self, checkpoint_name: str) -> Dict:
        """
        Resume pipeline execution from a saved checkpoint.
        
        Args:
            checkpoint_name: Name of checkpoint to resume from
            
        Returns:
            Execution result dictionary
        """
        self.logger.info(f"Resuming pipeline from checkpoint: {checkpoint_name}")
        
        # Load state
        state = self.state_manager.load_state()
        
        if not state:
            raise ValueError("No saved state found to resume from")
        
        # Determine which stages to run
        # Implementation depends on checkpoint strategy
        
        self.logger.warning("Resume from checkpoint not fully implemented in POC")
        return {"status": "not_implemented"}
