"""
Transformation Engine

Applies adstock and other marketing transformations to input data.
"""

import numpy as np
from typing import Dict
import logging


class TransformationEngine:
    """Apply transformations to marketing spend data."""
    
    def __init__(self, config: Dict):
        """
        Initialize transformation engine.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def apply_adstock(
        self,
        spend: np.ndarray,
        decay_rate: float,
        max_lag: int = None
    ) -> np.ndarray:
        """
        Apply geometric adstock transformation.
        
        The adstock effect models the carryover effect of marketing spend:
        effect[t] = spend[t] + decay_rate * effect[t-1]
        
        Args:
            spend: Array of marketing spend values
            decay_rate: Decay rate (0-1), higher means longer carryover
            max_lag: Maximum lag periods to consider
            
        Returns:
            Transformed spend with adstock effect
        """
        if max_lag is None:
            max_lag = self.config.get('adstock', {}).get('max_lag', 8)
        
        # Validate decay rate
        if not 0 <= decay_rate <= 1:
            raise ValueError(f"Decay rate must be between 0 and 1, got {decay_rate}")
        
        # Initialize adstocked array
        adstocked = np.zeros_like(spend, dtype=float)
        
        # Apply geometric decay
        for t in range(len(spend)):
            adstocked[t] = spend[t]
            
            # Add carryover effects from previous periods
            for lag in range(1, min(t + 1, max_lag + 1)):
                adstocked[t] += spend[t - lag] * (decay_rate ** lag)
        
        return adstocked
    
    def apply_adstock_vectorized(
        self,
        spend: np.ndarray,
        decay_rate: float
    ) -> np.ndarray:
        """
        Vectorized version of adstock transformation (faster).
        
        Args:
            spend: Array of marketing spend values
            decay_rate: Decay rate (0-1)
            
        Returns:
            Transformed spend with adstock effect
        """
        adstocked = np.zeros_like(spend, dtype=float)
        adstocked[0] = spend[0]
        
        for t in range(1, len(spend)):
            adstocked[t] = spend[t] + decay_rate * adstocked[t - 1]
        
        return adstocked
    
    def apply_lagged_adstock(
        self,
        spend: np.ndarray,
        decay_weights: np.ndarray
    ) -> np.ndarray:
        """
        Apply adstock with explicit lag weights.
        
        Args:
            spend: Array of marketing spend values
            decay_weights: Array of weights for each lag period
            
        Returns:
            Transformed spend with weighted adstock effect
        """
        max_lag = len(decay_weights)
        adstocked = np.zeros_like(spend, dtype=float)
        
        for t in range(len(spend)):
            for lag in range(min(t + 1, max_lag)):
                if lag < len(decay_weights):
                    adstocked[t] += spend[t - lag] * decay_weights[lag]
        
        return adstocked
    
    def reverse_adstock(
        self,
        adstocked: np.ndarray,
        decay_rate: float
    ) -> np.ndarray:
        """
        Reverse the adstock transformation to get original spend.
        
        Args:
            adstocked: Adstocked values
            decay_rate: Decay rate used in original transformation
            
        Returns:
            Original spend values
        """
        spend = np.zeros_like(adstocked, dtype=float)
        spend[0] = adstocked[0]
        
        for t in range(1, len(adstocked)):
            spend[t] = adstocked[t] - decay_rate * adstocked[t - 1]
        
        return spend
