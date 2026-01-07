"""
Baseline Agent

Estimates baseline sales, sets priors, and defines constraints for MMM modeling.
"""

import pandas as pd
import numpy as np
import json
import yaml
from pathlib import Path
from typing import Dict, List
from statsmodels.tsa.seasonal import seasonal_decompose
import logging

from .priors import PriorEstimator
from .constraints import ConstraintBuilder


class BaselineAgent:
    """
    Agent responsible for baseline estimation and prior specification.
    
    This agent:
    - Estimates baseline sales (organic sales without marketing)
    - Sets priors for model parameters based on domain knowledge
    - Defines constraints for optimization
    - Outputs structured priors for MMM
    """
    
    def __init__(
        self,
        config_path: str = "config/priors.yaml",
        global_config_path: str = "config/global.yaml"
    ):
        """
        Initialize the Baseline Agent.
        
        Args:
            config_path: Path to priors configuration
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
        
        self.prior_estimator = PriorEstimator(self.config)
        self.constraint_builder = ConstraintBuilder(self.config)
        
        self.baseline_estimates = None
        self.priors = None
        self.constraints = None
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def execute(
        self,
        sales_data_path: str,
        event_metadata_path: str = None
    ) -> Dict:
        """
        Execute the baseline estimation workflow.
        
        Args:
            sales_data_path: Path to sales time series data
            event_metadata_path: Optional path to event metadata from trend scanner
            
        Returns:
            Dictionary containing execution results and artifact paths
        """
        self.logger.info("Starting Baseline Agent execution")
        
        # Step 1: Load data
        sales_df = pd.read_csv(sales_data_path, sep=None, engine='python')
        
        # Parse date column
        date_col = self.mapping.get('date_column', 'date')
        if date_col in sales_df.columns:
             sales_df['date'] = pd.to_datetime(sales_df[date_col])
        else:
             sales_df['date'] = pd.to_datetime(sales_df['date'])
             
        self.logger.info(f"Loaded sales data with {len(sales_df)} periods")
        
        # Step 2: Load event metadata if available
        event_metadata = None
        if event_metadata_path and Path(event_metadata_path).exists():
            with open(event_metadata_path, 'r') as f:
                event_metadata = json.load(f)
        
        # Step 3: Estimate baseline sales
        self.baseline_estimates = self._estimate_baseline(sales_df, event_metadata)
        self.logger.info("Baseline estimation completed")
        
        # Step 4: Set priors for model parameters
        self.priors = self.prior_estimator.estimate_priors(
            sales_df, self.baseline_estimates
        )
        self.logger.info(f"Estimated priors for {len(self.priors.get('channels', {}))} channels")
        
        # Step 5: Build constraints
        self.constraints = self.constraint_builder.build_constraints(sales_df)
        self.logger.info("Built model constraints")
        
        # Step 6: Persist outputs
        output_paths = self._persist_outputs()
        
        self.logger.info("Baseline Agent execution completed")
        
        return {
            "status": "success",
            "baseline_mean": float(np.mean(self.baseline_estimates['baseline'])),
            "n_channels": len(self.priors.get('channels', {})),
            "output_paths": output_paths
        }
    
    def _estimate_baseline(
        self,
        sales_df: pd.DataFrame,
        event_metadata: Dict = None
    ) -> pd.DataFrame:
        """
        Estimate baseline sales (organic sales without marketing).
        
        Args:
            sales_df: Sales time series dataframe
            event_metadata: Optional metadata about events and seasonality
            
        Returns:
            DataFrame with baseline estimates
        """
        method = self.config['baseline']['method']
        
        sales_col = 'total_sales'
        if 'output_variable' in self.mapping:
             sales_col = self.mapping['output_variable']['column']
        elif 'sales' in sales_df.columns:
             sales_col = 'sales'
        elif 'total_sales' in sales_df.columns:
             sales_col = 'total_sales'
        
        result_df = sales_df[['date']].copy()
        
        if method == 'median':
            # Simple median baseline
            baseline = np.median(sales_df[sales_col])
            result_df['baseline'] = baseline
            
        elif method == 'mean':
            # Simple mean baseline
            baseline = np.mean(sales_df[sales_col])
            result_df['baseline'] = baseline
            
        elif method == 'regression':
            # Time-based regression for baseline trend
            sales_df['time_index'] = range(len(sales_df))
            from sklearn.linear_model import LinearRegression
            
            model = LinearRegression()
            X = sales_df[['time_index']].values
            y = sales_df[sales_col].values
            model.fit(X, y)
            
            result_df['baseline'] = model.predict(X)

        elif method == 'boosting':
            # Gradient Boosting (Non-linear Trend + Seasonality capability)
            sales_df['time_index'] = range(len(sales_df))
            from sklearn.ensemble import GradientBoostingRegressor
            
            # Use strict regularization to avoid fitting the marketing spikes
            model = GradientBoostingRegressor(
                n_estimators=100, 
                learning_rate=0.05, 
                max_depth=3,
                random_state=42,
                loss='absolute_error' # Robust to outliers (marketing spikes)
            )
            X = sales_df[['time_index']].values
            y = sales_df[sales_col].values
            model.fit(X, y)
            
            result_df['baseline'] = model.predict(X)
        
        else:
            # Default to median
            baseline = np.median(sales_df[sales_col])
            result_df['baseline'] = baseline
        
        # Adjust for seasonality if available
        if event_metadata and event_metadata.get('seasonality', {}).get('has_seasonality'):
            try:
                decomposition = seasonal_decompose(
                    sales_df[sales_col],
                    model=self.config['baseline']['decomposition']['model'],
                    period=52,
                    extrapolate_trend='freq'
                )
                result_df['baseline'] = decomposition.trend.fillna(method='bfill').fillna(method='ffill')
            except Exception as e:
                self.logger.warning(f"Could not apply seasonal adjustment: {e}")
        
        result_df['actual_sales'] = sales_df[sales_col].values
        result_df['incremental_sales'] = result_df['actual_sales'] - result_df['baseline']
        
        return result_df
    
    def _persist_outputs(self) -> Dict[str, str]:
        """Save baseline estimates and priors to disk."""
        output_dir = Path("data/processed")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save baseline estimates
        baseline_path = output_dir / "baseline_estimates.csv"
        self.baseline_estimates.to_csv(baseline_path, index=False)
        
        # Save priors
        priors_path = output_dir / "priors.json"
        with open(priors_path, 'w') as f:
            json.dump(self.priors, f, indent=2)
        
        # Save constraints
        constraints_path = output_dir / "constraints.json"
        with open(constraints_path, 'w') as f:
            json.dump(self.constraints, f, indent=2)
        
        return {
            "baseline_estimates": str(baseline_path),
            "priors": str(priors_path),
            "constraints": str(constraints_path)
        }
    
    def get_baseline_for_period(self, date: pd.Timestamp) -> float:
        """
        Get baseline estimate for a specific period.
        
        Args:
            date: Date to get baseline for
            
        Returns:
            Baseline sales estimate
        """
        if self.baseline_estimates is None:
            raise ValueError("Baseline estimation has not been executed yet")
        
        row = self.baseline_estimates[self.baseline_estimates['date'] == date]
        
        if len(row) == 0:
            raise ValueError(f"No baseline estimate found for date {date}")
        
        return float(row.iloc[0]['baseline'])
