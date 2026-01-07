"""
Constraint Builder

Builds constraints for model optimization.
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import logging


class ConstraintBuilder:
    """Build constraints for MMM and optimization."""
    
    def __init__(self, config: Dict):
        """
        Initialize constraint builder.
        
        Args:
            config: Priors/constraints configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def build_constraints(self, sales_df: pd.DataFrame) -> Dict:
        """
        Build all constraints for modeling.
        
        Args:
            sales_df: Sales and spend dataframe
            
        Returns:
            Dictionary of constraints
        """
        constraints = {
            'coefficients': self._build_coefficient_constraints(),
            'contributions': self._build_contribution_constraints(),
            'saturation': self._build_saturation_constraints(),
            'adstock': self._build_adstock_constraints()
        }
        
        return constraints
    
    def _build_coefficient_constraints(self) -> Dict:
        """Build constraints for model coefficients."""
        coef_config = self.config.get('coefficient_constraints', {})
        
        return {
            'non_negative': coef_config.get('non_negative', True),
            'contribution_min': coef_config.get('contribution_ranges', {}).get('min_contribution', 0.0),
            'contribution_max': coef_config.get('contribution_ranges', {}).get('max_contribution', 0.5)
        }
    
    def _build_contribution_constraints(self) -> Dict:
        """Build constraints for channel contributions."""
        # These ensure realistic contribution ranges
        return {
            'min_contribution': 0.0,
            'max_contribution': 1.0,
            'sum_max': 1.0  # All contributions should sum to <= 100%
        }
    
    def _build_saturation_constraints(self) -> Dict:
        """Build constraints for saturation parameters."""
        saturation_config = self.config.get('saturation', {})
        
        return {
            'alpha': {
                'min': saturation_config.get('alpha', {}).get('min', 0.5),
                'max': saturation_config.get('alpha', {}).get('max', 10.0)
            },
            'gamma': {
                'min': saturation_config.get('gamma', {}).get('min', 0.1),
                'max': saturation_config.get('gamma', {}).get('max', 1.0)
            }
        }
    
    def _build_adstock_constraints(self) -> Dict:
        """Build constraints for adstock parameters."""
        adstock_config = self.config.get('adstock', {})
        
        return {
            'decay_rate': {
                'min': adstock_config.get('decay_rate', {}).get('min', 0.0),
                'max': adstock_config.get('decay_rate', {}).get('max', 0.95)
            },
            'max_lag': adstock_config.get('max_lag', 8)
        }
