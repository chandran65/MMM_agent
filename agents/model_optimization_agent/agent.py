"""
Model Optimization Agent

Applies transformations (adstock, saturation), trains MMM/MMX models,
and calculates contributions and response curves.
"""

import pandas as pd
import numpy as np
import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
import logging
import pickle

from .transformations import TransformationEngine
from .saturation import SaturationFunctions
from .trainer import ModelTrainer


class ModelOptimizationAgent:
    """
    Agent responsible for MMM/MMX model training and optimization.
    
    This agent:
    - Applies adstock transformations to marketing spend
    - Applies saturation functions (Hill + Weibull)
    - Trains MMM regression models
    - Calculates channel contributions
    - Generates response curves for each channel
    """
    
    def __init__(
        self,
        config_path: str = "config/priors.yaml",
        global_config_path: str = "config/global.yaml"
    ):
        """
        Initialize the Model Optimization Agent.
        
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
        
        self.transformation_engine = TransformationEngine(self.config)
        self.saturation_functions = SaturationFunctions(self.config)
        self.trainer = ModelTrainer(self.config, self.global_config)
        
        self.model = None
        self.contributions = None
        self.response_curves = None
        self.model_metrics = None
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def execute(
        self,
        sales_data_path: str,
        priors_path: str,
        baseline_path: str
    ) -> Dict:
        """
        Execute the model optimization workflow.
        
        Args:
            sales_data_path: Path to sales and spend data
            priors_path: Path to priors JSON
            baseline_path: Path to baseline estimates
            
        Returns:
            Dictionary containing execution results and artifact paths
        """
        self.logger.info("Starting Model Optimization Agent execution")
        
        # Step 1: Load data
        sales_df = pd.read_csv(sales_data_path, sep=None, engine='python')
        
        # Handle date column from mapping
        date_col = 'date'
        if 'date_column' in self.mapping:
             date_col = self.mapping['date_column']
        
        if date_col in sales_df.columns:
             sales_df['date'] = pd.to_datetime(sales_df[date_col])
        else:
             # Fallback
             sales_df['date'] = pd.to_datetime(sales_df['date'])
        
        with open(priors_path, 'r') as f:
            priors = json.load(f)
        
        baseline_df = pd.read_csv(baseline_path)
        
        self.logger.info(f"Loaded data with {len(sales_df)} periods")
        
        # Step 2: Identify channel columns
        channels = self._identify_channels(sales_df)
        self.logger.info(f"Identified {len(channels)} marketing channels: {channels}")
        
        # Step 3: Apply transformations
        transformed_df = self._apply_transformations(sales_df, channels, priors)
        self.logger.info("Applied adstock and saturation transformations")
        
        # Step 4: Train MMM model
        self.model, self.model_metrics = self.trainer.train_model(
            transformed_df, baseline_df, channels
        )
        self.logger.info(f"Model trained with R² = {self.model_metrics['r_squared']:.3f}")
        
        # Step 5: Calculate contributions
        self.contributions = self._calculate_contributions(
            transformed_df, channels, sales_df
        )
        self.logger.info("Calculated channel contributions")
        
        # Step 6: Generate response curves
        self.response_curves = self._generate_response_curves(
            sales_df, channels, priors
        )
        self.logger.info("Generated response curves")
        
        # Step 7: Persist outputs
        output_paths = self._persist_outputs(channels)
        
        self.logger.info("Model Optimization Agent execution completed")
        
        return {
            "status": "success",
            "model_metrics": self.model_metrics,
            "n_channels": len(channels),
            "total_contribution": float(sum(self.contributions['total_contribution'].values())),
            "output_paths": output_paths
        }
    
    def _identify_channels(self, df: pd.DataFrame) -> List[str]:
        """
        Identify marketing channel columns from dataframe.
        
        Args:
            df: Sales dataframe
            
        Returns:
            List of channel names
        """
        columns = df.columns
        channels = []
        
        # Check mapping first
        if 'input_variables' in self.mapping and 'media' in self.mapping['input_variables']:
             media_vars = self.mapping['input_variables']['media']
             for media in media_vars:
                 channels.append(media['name'])
             return channels
        
        for col in columns:
            if col.endswith('_spend'):
                channel_name = col.replace('_spend', '').upper()
                channels.append(channel_name)
        
        # If no spend columns found, try to identify numeric columns that aren't date/sales
        if not channels:
            exclude_cols = ['date', 'sales', 'total_sales', 'volume', 'total_volume', 'id']
            # Identify numeric columns
            numeric_cols = [c for c in columns if c.lower() not in exclude_cols and pd.api.types.is_numeric_dtype(df[c])]
            
            channels = [c.upper() for c in numeric_cols]
            self.logger.info(f"No _spend columns found. Inferred channels: {channels}")

        # If still no channels, try from priors config
        if not channels:
            channels = list(self.config.get('channels', {}).keys())
        
        return channels
    
    def _apply_transformations(
        self,
        sales_df: pd.DataFrame,
        channels: List[str],
        priors: Dict
    ) -> pd.DataFrame:
        """
        Apply adstock and saturation transformations to spend data.
        
        Args:
            sales_df: Sales and spend dataframe
            channels: List of channel names
            priors: Priors dictionary
            
        Returns:
            DataFrame with transformed features
        """
        transformed_df = sales_df.copy()
        
        for channel in channels:
            spend_col = f'{channel.lower()}_spend'
            
            # Resolve spend column from mapping if available
            if 'input_variables' in self.mapping and 'media' in self.mapping['input_variables']:
                 for media in self.mapping['input_variables']['media']:
                     if media['name'] == channel:
                         spend_col = media['column']
                         break
            
            if spend_col not in transformed_df.columns:
                # Fallback to direct channel name
                if channel.lower() in transformed_df.columns:
                    spend_col = channel.lower()
                else:
                    self.logger.warning(f"Missing spend column for {channel}")
                    continue
            
            # Get channel priors
            channel_priors = priors.get('channels', {}).get(channel, {})
            
            # Apply adstock transformation
            adstock_rate = np.mean(channel_priors.get('adstock_range', [0.5, 0.5]))
            adstocked = self.transformation_engine.apply_adstock(
                transformed_df[spend_col].values,
                decay_rate=adstock_rate
            )
            
            # Apply saturation (Hill function)
            alpha = np.mean(channel_priors.get('saturation_alpha_range', [2.0, 2.0]))
            gamma = np.mean(channel_priors.get('saturation_gamma_range', [0.5, 0.5]))
            
            saturated = self.saturation_functions.hill_saturation(
                adstocked,
                alpha=alpha,
                gamma=gamma
            )
            
            # Add transformed column
            transformed_df[f'{channel}_transformed'] = saturated
        
        return transformed_df
    
    def _calculate_contributions(
        self,
        transformed_df: pd.DataFrame,
        channels: List[str],
        original_df: pd.DataFrame
    ) -> Dict:
        """
        Calculate contribution of each channel to sales.
        
        Args:
            transformed_df: DataFrame with transformed features
            channels: List of channel names
            original_df: Original sales dataframe
            
        Returns:
            Dictionary of contributions
        """
        contributions = {
            'channel_contributions': {},
            'total_contribution': {},
            'contribution_pct': {}
        }
        
        # Get total sales
        sales_col = 'sales' if 'sales' in original_df.columns else 'total_sales'
        total_sales = original_df[sales_col].sum()
        
        for channel in channels:
            transformed_col = f'{channel}_transformed'
            
            if transformed_col not in transformed_df.columns:
                continue
            
            # Get coefficient from model
            if hasattr(self.model, 'coef_'):
                # Find coefficient index
                feature_cols = [c for c in transformed_df.columns if c.endswith('_transformed')]
                if transformed_col in feature_cols:
                    coef_idx = feature_cols.index(transformed_col)
                    coef = self.model.coef_[coef_idx]
                    
                    # Calculate contribution
                    channel_contribution = (
                        transformed_df[transformed_col].values * coef
                    ).sum()
                    
                    contributions['channel_contributions'][channel] = float(channel_contribution)
                    contributions['total_contribution'][channel] = float(channel_contribution)
                    contributions['contribution_pct'][channel] = float(
                        (channel_contribution / total_sales) * 100 if total_sales > 0 else 0
                    )
        
        return contributions
    
    def _generate_response_curves(
        self,
        sales_df: pd.DataFrame,
        channels: List[str],
        priors: Dict
    ) -> Dict:
        """
        Generate response curves for each channel.
        
        Args:
            sales_df: Sales and spend dataframe
            channels: List of channel names
            priors: Priors dictionary
            
        Returns:
            Dictionary of response curves
        """
        response_curves = {}
        
        for channel in channels:
            spend_col = f'{channel.lower()}_spend'
            
            # Resolve spend column from mapping if available
            if 'input_variables' in self.mapping and 'media' in self.mapping['input_variables']:
                 for media in self.mapping['input_variables']['media']:
                     if media['name'] == channel:
                         spend_col = media['column']
                         break
            
            if spend_col not in sales_df.columns:
                # Fallback to direct channel name
                if channel.lower() in sales_df.columns:
                    spend_col = channel.lower()
                else:
                    continue
            
            # Get channel priors
            channel_priors = priors.get('channels', {}).get(channel, {})
            
            # Get spend range
            current_spend = sales_df[spend_col].values
            spend_min = 0
            spend_max = np.max(current_spend) * 2  # Up to 2x current max
            
            # Generate spend points
            spend_points = np.linspace(spend_min, spend_max, 100)
            
            # Apply transformations
            adstock_rate = np.mean(channel_priors.get('adstock_range', [0.5, 0.5]))
            alpha = np.mean(channel_priors.get('saturation_alpha_range', [2.0, 2.0]))
            gamma = np.mean(channel_priors.get('saturation_gamma_range', [0.5, 0.5]))
            
            # Calculate response for each spend point
            responses = []
            for spend in spend_points:
                # Simplified: direct saturation without time series adstock
                response = self.saturation_functions.hill_saturation(
                    np.array([spend]),
                    alpha=alpha,
                    gamma=gamma * np.max(current_spend) if np.max(current_spend) > 0 else gamma
                )[0]
                responses.append(response)
            
            response_curves[channel] = {
                'spend': spend_points.tolist(),
                'response': responses,
                'current_spend_avg': float(np.mean(current_spend)),
                'optimal_efficiency_point': float(gamma * np.max(current_spend))
            }
        
        return response_curves
    
    def _persist_outputs(self, channels: List[str]) -> Dict[str, str]:
        """Save model, contributions, and response curves to disk."""
        
        # Save trained model
        model_dir = Path("models/trained")
        model_dir.mkdir(parents=True, exist_ok=True)
        model_path = model_dir / "mmm_model.pkl"
        
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        
        # Save model metrics
        metrics_path = model_dir / "model_metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(self.model_metrics, f, indent=2)
        
        # Save contributions
        contrib_dir = Path("artifacts/contributions")
        contrib_dir.mkdir(parents=True, exist_ok=True)
        contrib_path = contrib_dir / "channel_contributions.json"
        
        with open(contrib_path, 'w') as f:
            json.dump(self.contributions, f, indent=2)
        
        # Save contribution table as CSV
        contrib_df = pd.DataFrame({
            'channel': list(self.contributions['total_contribution'].keys()),
            'contribution': list(self.contributions['total_contribution'].values()),
            'contribution_pct': list(self.contributions['contribution_pct'].values())
        })
        contrib_csv_path = contrib_dir / "channel_contributions.csv"
        contrib_df.to_csv(contrib_csv_path, index=False)
        
        # Save response curves
        curves_dir = Path("artifacts/curves")
        curves_dir.mkdir(parents=True, exist_ok=True)
        curves_path = curves_dir / "response_curves.json"
        
        with open(curves_path, 'w') as f:
            json.dump(self.response_curves, f, indent=2)
        
        # Save response curves CSV
        for channel, curve_data in self.response_curves.items():
            curve_df = pd.DataFrame({
                'spend': curve_data['spend'],
                'response': curve_data['response']
            })
            curve_csv_path = curves_dir / f"{channel}_response_curve.csv"
            curve_df.to_csv(curve_csv_path, index=False)
        
        # Update model registry
        self._update_model_registry(str(model_path), channels)
        
        return {
            "model": str(model_path),
            "metrics": str(metrics_path),
            "contributions_json": str(contrib_path),
            "contributions_csv": str(contrib_csv_path),
            "response_curves": str(curves_path)
        }
    
    def _update_model_registry(self, model_path: str, channels: List[str]) -> None:
        """Update the model registry with new model information."""
        registry_path = Path("models/registry.json")
        
        # Load existing registry or create new
        if registry_path.exists():
            with open(registry_path, 'r') as f:
                registry = json.load(f)
        else:
            registry = {"models": []}
        
        # Add new model entry
        from datetime import datetime
        model_entry = {
            "model_id": f"mmm_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "model_path": model_path,
            "created_at": datetime.now().isoformat(),
            "channels": channels,
            "metrics": self.model_metrics,
            "status": "active"
        }
        
        registry["models"].append(model_entry)
        
        # Save updated registry
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)
