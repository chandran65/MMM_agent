"""
Prior Estimator

Estimates priors for model parameters based on domain knowledge and data.
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import logging


class PriorEstimator:
    """Estimate priors for MMM parameters."""
    
    def __init__(self, config: Dict):
        """
        Initialize prior estimator.
        
        Args:
            config: Priors configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def estimate_priors(
        self,
        sales_df: pd.DataFrame,
        baseline_df: pd.DataFrame
    ) -> Dict:
        """
        Estimate priors for all model parameters.
        
        Args:
            sales_df: Sales and spend data
            baseline_df: Baseline estimates
            
        Returns:
            Dictionary of priors
        """
        priors = {
            'baseline': self._estimate_baseline_priors(baseline_df),
            'channels': self._estimate_channel_priors(sales_df),
            'saturation': self._get_saturation_priors(),
            'adstock': self._get_adstock_priors(),
            'regularization': self._get_regularization_priors()
        }
        
        return priors
    
    def _estimate_baseline_priors(self, baseline_df: pd.DataFrame) -> Dict:
        """Estimate priors for baseline component."""
        baseline_values = baseline_df['baseline'].values
        
        return {
            'mean': float(np.mean(baseline_values)),
            'std': float(np.std(baseline_values)),
            'min': float(np.min(baseline_values)),
            'max': float(np.max(baseline_values))
        }
    
    def _estimate_channel_priors(self, sales_df: pd.DataFrame) -> Dict:
        """
        Estimate priors for each marketing channel.
        
        Args:
            sales_df: Dataframe with sales and channel spend columns
            
        Returns:
            Dictionary of channel priors
        """
        channel_priors = {}
        
        # Get channel configuration from config
        channel_config = self.config.get('channels', {})
        
        for channel_name, channel_info in channel_config.items():
            # Look for spend column
            spend_col = f'{channel_name.lower()}_spend'
            
            if spend_col in sales_df.columns:
                spend_values = sales_df[spend_col].values
                
                channel_priors[channel_name] = {
                    'adstock_range': channel_info['adstock_range'],
                    'saturation_alpha_range': channel_info['saturation_alpha_range'],
                    'saturation_gamma_range': channel_info['saturation_gamma_range'],
                    'expected_roi': channel_info['roi_expected'],
                    'spend_mean': float(np.mean(spend_values)),
                    'spend_std': float(np.std(spend_values)),
                    'spend_max': float(np.max(spend_values))
                }
            else:
                # Use default priors if data not available
                channel_priors[channel_name] = {
                    'adstock_range': channel_info['adstock_range'],
                    'saturation_alpha_range': channel_info['saturation_alpha_range'],
                    'saturation_gamma_range': channel_info['saturation_gamma_range'],
                    'expected_roi': channel_info['roi_expected']
                }
        
        return channel_priors
    
    def _get_saturation_priors(self) -> Dict:
        """Get saturation function priors from config."""
        return self.config.get('saturation', {})
    
    def _get_adstock_priors(self) -> Dict:
        """Get adstock transformation priors from config."""
        return self.config.get('adstock', {})
    
    def _get_regularization_priors(self) -> Dict:
        """Get regularization priors from config."""
        return self.config.get('regularization', {})
