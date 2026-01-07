"""
Budget Optimization Agent

Runs constrained optimization to find optimal budget allocation across channels.
"""

import pandas as pd
import numpy as np
import json
import yaml
from pathlib import Path
from typing import Dict, List
import logging

from .solver import OptimizationSolver
from .bounds import BoundsManager


class BudgetOptimizationAgent:
    """
    Agent responsible for budget optimization.
    
    This agent:
    - Loads response curves and model outputs
    - Applies channel bounds and business constraints
    - Runs constrained optimization (scipy SLSQP)
    - Generates optimized spend scenarios
    - Outputs recommendations
    """
    
    def __init__(
        self,
        config_path: str = "config/optimization.yaml",
        global_config_path: str = "config/global.yaml"
    ):
        """
        Initialize the Budget Optimization Agent.
        
        Args:
            config_path: Path to optimization configuration
            global_config_path: Path to global configuration
        """
        self.config = self._load_config(config_path)
        self.global_config = self._load_config(global_config_path)
        
        # Load variable mapping if exists
        mapping_path = "config/variable_mapping.yaml"
        self.mapping = {}
        if Path(mapping_path).exists():
             with open(mapping_path, 'r') as f:
                mapping_config = yaml.safe_load(f)
                if mapping_config:
                    self.mapping = mapping_config.get('variable_mapping', {})
                    
        self.logger = logging.getLogger(__name__)
        
        self.solver = OptimizationSolver(self.config)
        self.bounds_manager = BoundsManager(self.config)
        
        self.optimization_results = None
        self.scenarios = {}
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def execute(
        self,
        response_curves_path: str,
        current_spend_path: str = None
    ) -> Dict:
        """
        Execute the budget optimization workflow.
        
        Args:
            response_curves_path: Path to response curves JSON
            current_spend_path: Optional path to current spend data
            
        Returns:
            Dictionary containing execution results and artifact paths
        """
        self.logger.info("Starting Budget Optimization Agent execution")
        
        # Step 1: Load response curves
        with open(response_curves_path, 'r') as f:
            response_curves = json.load(f)
        
        channels = list(response_curves.keys())
        self.logger.info(f"Loaded response curves for {len(channels)} channels")
        
        # Step 2: Get current spend (or use defaults)
        current_spend = self._get_current_spend(response_curves, current_spend_path)
        
        # Step 3: Get total budget from config
        total_budget = self.config['optimization']['budget']['total_budget']
        self.logger.info(f"Total budget: ${total_budget:,.0f}")
        
        # Step 4: Set up bounds and constraints
        bounds, constraints = self.bounds_manager.get_bounds_and_constraints(
            channels, total_budget, current_spend
        )
        
        # Step 5: Run optimization for base scenario
        base_result = self.solver.optimize(
            response_curves,
            total_budget,
            bounds,
            constraints,
            current_spend
        )
        
        self.scenarios['base'] = base_result
        self.logger.info(f"Base optimization completed. Expected lift: {base_result['expected_lift']:.2%}")
        
        # Step 6: Run optimization for additional scenarios
        scenario_configs = self.config['optimization'].get('scenarios', {})
        
        for scenario_name, scenario_config in scenario_configs.items():
            if scenario_name == 'base':
                continue
            
            scenario_budget = total_budget * scenario_config['multiplier']
            
            scenario_result = self.solver.optimize(
                response_curves,
                scenario_budget,
                bounds,
                constraints,
                current_spend
            )
            
            self.scenarios[scenario_name] = scenario_result
            self.logger.info(
                f"{scenario_name.capitalize()} scenario completed. "
                f"Budget: ${scenario_budget:,.0f}, Expected lift: {scenario_result['expected_lift']:.2%}"
            )
        
        # Step 7: Consolidate results
        self.optimization_results = self._consolidate_results(channels)
        
        # Step 8: Persist outputs
        output_paths = self._persist_outputs()
        
        self.logger.info("Budget Optimization Agent execution completed")
        
        return {
            "status": "success",
            "n_scenarios": len(self.scenarios),
            "base_expected_lift": self.scenarios['base']['expected_lift'],
            "output_paths": output_paths
        }
    
    def _get_current_spend(
        self,
        response_curves: Dict,
        current_spend_path: str = None
    ) -> Dict[str, float]:
        """
        Get current spend for each channel.
        
        Args:
            response_curves: Response curves dictionary
            current_spend_path: Optional path to current spend data
            
        Returns:
            Dictionary of current spend by channel
        """
        if current_spend_path and Path(current_spend_path).exists():
            current_df = pd.read_csv(current_spend_path, sep=None, engine='python')
            current_spend = {}
            
            for channel in response_curves.keys():
                spend_col = f'{channel.lower()}_spend'
                
                # Resolve spend column from mapping if available
                if 'input_variables' in self.mapping and 'media' in self.mapping['input_variables']:
                     for media in self.mapping['input_variables']['media']:
                         if media['name'] == channel:
                             spend_col = media['column']
                             break
                
                if spend_col in current_df.columns:
                    current_spend[channel] = float(current_df[spend_col].mean())
                else:
                    current_spend[channel] = response_curves[channel].get(
                        'current_spend_avg', 0
                    )
        else:
            # Use spend from response curves
            current_spend = {
                channel: data.get('current_spend_avg', 0)
                for channel, data in response_curves.items()
            }
        
        return current_spend
    
    def _consolidate_results(self, channels: List[str]) -> pd.DataFrame:
        """
        Consolidate optimization results across scenarios.
        
        Args:
            channels: List of channel names
            
        Returns:
            DataFrame with consolidated results
        """
        results_data = []
        
        for scenario_name, scenario_result in self.scenarios.items():
            optimal_spend = scenario_result['optimal_spend']
            
            for channel in channels:
                results_data.append({
                    'scenario': scenario_name,
                    'channel': channel,
                    'optimized_spend': optimal_spend.get(channel, 0),
                    'current_spend': scenario_result.get('current_spend', {}).get(channel, 0),
                    'change_pct': scenario_result.get('spend_changes', {}).get(channel, 0),
                    'expected_response': scenario_result.get('channel_responses', {}).get(channel, 0)
                })
        
        return pd.DataFrame(results_data)
    
    def _persist_outputs(self) -> Dict[str, str]:
        """Save optimization results to disk."""
        roi_dir = Path("artifacts/roi")
        roi_dir.mkdir(parents=True, exist_ok=True)
        
        # Save recommendations CSV
        recommendations_path = roi_dir / "optimization_recommendations.csv"
        self.optimization_results.to_csv(recommendations_path, index=False)
        
        # Save scenario comparison
        scenario_comparison = self._create_scenario_comparison()
        comparison_path = roi_dir / "scenario_comparison.json"
        
        with open(comparison_path, 'w') as f:
            json.dump(scenario_comparison, f, indent=2)
        
        # Save Excel version
        excel_path = roi_dir / "scenario_comparison.xlsx"
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            self.optimization_results.to_excel(writer, sheet_name='Recommendations', index=False)
            
            # Add scenario summary sheet
            scenario_df = pd.DataFrame([
                {
                    'scenario': name,
                    'total_budget': result.get('total_budget', 0),
                    'expected_sales': result.get('expected_sales', 0),
                    'expected_lift': result.get('expected_lift', 0),
                    'roi': result.get('overall_roi', 0)
                }
                for name, result in self.scenarios.items()
            ])
            scenario_df.to_excel(writer, sheet_name='Scenario Summary', index=False)
        
        self.logger.info(f"Saved optimization results to {roi_dir}")
        
        return {
            "recommendations": str(recommendations_path),
            "scenario_comparison": str(comparison_path),
            "excel_report": str(excel_path)
        }
    
    def _create_scenario_comparison(self) -> Dict:
        """Create scenario comparison dictionary."""
        comparison = {}
        
        for scenario_name, result in self.scenarios.items():
            comparison[scenario_name] = {
                'total_budget': result.get('total_budget', 0),
                'expected_sales': result.get('expected_sales', 0),
                'expected_lift': result.get('expected_lift', 0),
                'overall_roi': result.get('overall_roi', 0),
                'optimal_allocation': result.get('optimal_spend', {}),
                'vs_current': result.get('spend_changes', {})
            }
        
        return comparison
