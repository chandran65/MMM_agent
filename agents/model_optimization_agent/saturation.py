"""
Saturation Functions

Implements Hill, Weibull, and other saturation functions for diminishing returns.
"""

import numpy as np
from typing import Dict, Callable
import logging


class SaturationFunctions:
    """Saturation functions for modeling diminishing returns."""
    
    def __init__(self, config: Dict):
        """
        Initialize saturation functions.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def hill_saturation(
        self,
        spend: np.ndarray,
        alpha: float,
        gamma: float
    ) -> np.ndarray:
        """
        Apply Hill saturation function.
        
        The Hill function models diminishing returns:
        response = spend^alpha / (gamma^alpha + spend^alpha)
        
        Args:
            spend: Marketing spend values
            alpha: Shape parameter (controls curve steepness)
            gamma: Half-saturation point (spend at 50% of max response)
            
        Returns:
            Saturated response values (0-1 scale)
        """
        # Validate parameters
        if alpha <= 0:
            raise ValueError(f"Alpha must be positive, got {alpha}")
        if gamma <= 0:
            raise ValueError(f"Gamma must be positive, got {gamma}")
        
        # Avoid division by zero
        spend = np.maximum(spend, 1e-10)
        
        # Apply Hill function
        numerator = np.power(spend, alpha)
        denominator = np.power(gamma, alpha) + numerator
        
        response = numerator / denominator
        
        return response
    
    def weibull_saturation(
        self,
        spend: np.ndarray,
        shape: float,
        scale: float
    ) -> np.ndarray:
        """
        Apply Weibull saturation function.
        
        The Weibull CDF can model S-shaped saturation curves:
        response = 1 - exp(-(spend/scale)^shape)
        
        Args:
            spend: Marketing spend values
            shape: Shape parameter (k)
            scale: Scale parameter (λ)
            
        Returns:
            Saturated response values (0-1 scale)
        """
        # Validate parameters
        if shape <= 0:
            raise ValueError(f"Shape must be positive, got {shape}")
        if scale <= 0:
            raise ValueError(f"Scale must be positive, got {scale}")
        
        # Apply Weibull CDF
        response = 1 - np.exp(-np.power(spend / scale, shape))
        
        return response
    
    def logistic_saturation(
        self,
        spend: np.ndarray,
        growth_rate: float,
        midpoint: float
    ) -> np.ndarray:
        """
        Apply logistic saturation function.
        
        The logistic function:
        response = 1 / (1 + exp(-growth_rate * (spend - midpoint)))
        
        Args:
            spend: Marketing spend values
            growth_rate: Growth rate parameter
            midpoint: Inflection point
            
        Returns:
            Saturated response values (0-1 scale)
        """
        response = 1 / (1 + np.exp(-growth_rate * (spend - midpoint)))
        
        return response
    
    def negative_exponential_saturation(
        self,
        spend: np.ndarray,
        rate: float
    ) -> np.ndarray:
        """
        Apply negative exponential saturation.
        
        Simple exponential approach to saturation:
        response = 1 - exp(-rate * spend)
        
        Args:
            spend: Marketing spend values
            rate: Decay rate parameter
            
        Returns:
            Saturated response values (0-1 scale)
        """
        if rate <= 0:
            raise ValueError(f"Rate must be positive, got {rate}")
        
        response = 1 - np.exp(-rate * spend)
        
        return response
    
    def get_marginal_response(
        self,
        saturation_func: Callable,
        spend: float,
        **kwargs
    ) -> float:
        """
        Calculate marginal response (derivative) at a given spend level.
        
        Args:
            saturation_func: Saturation function to use
            spend: Spend level to calculate marginal response at
            **kwargs: Parameters for the saturation function
            
        Returns:
            Marginal response value
        """
        # Use numerical differentiation
        delta = spend * 0.001  # 0.1% change
        
        response_at_spend = saturation_func(
            np.array([spend]), **kwargs
        )[0]
        
        response_at_spend_plus = saturation_func(
            np.array([spend + delta]), **kwargs
        )[0]
        
        marginal = (response_at_spend_plus - response_at_spend) / delta
        
        return marginal
    
    def get_optimal_spend(
        self,
        saturation_func: Callable,
        target_efficiency: float,
        max_spend: float,
        **kwargs
    ) -> float:
        """
        Find optimal spend for a target efficiency level.
        
        Args:
            saturation_func: Saturation function to use
            target_efficiency: Target marginal efficiency (e.g., 0.5)
            max_spend: Maximum spend to consider
            **kwargs: Parameters for the saturation function
            
        Returns:
            Optimal spend level
        """
        # Use binary search to find optimal spend
        spend_range = np.linspace(0, max_spend, 1000)
        
        for spend in spend_range:
            marginal = self.get_marginal_response(
                saturation_func, spend, **kwargs
            )
            
            if marginal <= target_efficiency:
                return float(spend)
        
        return float(max_spend)
