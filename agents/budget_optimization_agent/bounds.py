"""
Bounds Manager

Manages bounds and constraints for optimization.
"""

import numpy as np
from typing import Dict, List, Tuple
import logging


class BoundsManager:
    """Manage bounds and constraints for budget optimization."""
    
    def __init__(self, config: Dict):
        """
        Initialize bounds manager.
        
        Args:
            config: Optimization configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def get_bounds_and_constraints(
        self,
        channels: List[str],
        total_budget: float,
        current_spend: Dict[str, float]
    ) -> Tuple[List[Tuple], List[Dict]]:
        """
        Get bounds and constraints for optimization.
        
        Args:
            channels: List of channel names
            total_budget: Total budget
            current_spend: Current spend by channel
            
        Returns:
            Tuple of (bounds list, constraints list)
        """
        bounds = self._get_channel_bounds(channels, total_budget)
        constraints = self._get_optimization_constraints(channels, total_budget, current_spend)
        
        return bounds, constraints
    
    def _get_channel_bounds(
        self,
        channels: List[str],
        total_budget: float
    ) -> List[Tuple[float, float]]:
        """
        Get spend bounds for each channel.
        
        Args:
            channels: List of channel names
            total_budget: Total budget
            
        Returns:
            List of (min, max) tuples for each channel
        """
        bounds = []
        budget_config = self.config['optimization']['budget']
        channel_bounds_config = budget_config.get('channel_bounds', {})
        channel_constraints = budget_config.get('channel_constraints', {})
        
        for channel in channels:
            # Get percentage bounds
            channel_bound = channel_bounds_config.get(channel, {'min': 0.05, 'max': 0.50})
            
            min_pct = channel_bound.get('min', 0.0)
            max_pct = channel_bound.get('max', 1.0)
            
            min_spend = total_budget * min_pct
            max_spend = total_budget * max_pct
            
            # Override with absolute constraints if specified
            if channel in channel_constraints:
                abs_min = channel_constraints[channel].get('min_absolute_spend')
                if abs_min is not None:
                    min_spend = max(min_spend, abs_min)
            
            bounds.append((min_spend, max_spend))
        
        return bounds
    
    def _get_optimization_constraints(
        self,
        channels: List[str],
        total_budget: float,
        current_spend: Dict[str, float]
    ) -> List[Dict]:
        """
        Get optimization constraints.
        
        Args:
            channels: List of channel names
            total_budget: Total budget
            current_spend: Current spend by channel
            
        Returns:
            List of constraint dictionaries for scipy
        """
        constraints = []
        
        # Constraint 1: Total spend must equal total budget
        constraints.append({
            'type': 'eq',
            'fun': lambda x: np.sum(x) - total_budget
        })
        
        # Constraint 2: Minimum budget utilization
        min_utilization = self.config['optimization']['constraints'].get(
            'min_budget_utilization', 0.9
        )
        
        constraints.append({
            'type': 'ineq',
            'fun': lambda x: np.sum(x) - (total_budget * min_utilization)
        })
        
        # Constraint 3: Maximum change from current spend
        max_change = self.config['optimization']['constraints'].get(
            'max_change_from_current', 0.3
        )
        
        for i, channel in enumerate(channels):
            current = current_spend.get(channel, 0)
            
            if current > 0:
                # Max increase constraint
                constraints.append({
                    'type': 'ineq',
                    'fun': lambda x, idx=i, curr=current: 
                        (curr * (1 + max_change)) - x[idx]
                })
                
                # Max decrease constraint
                constraints.append({
                    'type': 'ineq',
                    'fun': lambda x, idx=i, curr=current: 
                        x[idx] - (curr * (1 - max_change))
                })
        
        return constraints
    
    def validate_allocation(
        self,
        allocation: Dict[str, float],
        total_budget: float,
        channels: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that allocation meets all constraints.
        
        Args:
            allocation: Spend allocation by channel
            total_budget: Total budget
            channels: List of channel names
            
        Returns:
            Tuple of (is_valid, list of violations)
        """
        violations = []
        
        # Check total budget
        total_allocated = sum(allocation.values())
        if abs(total_allocated - total_budget) / total_budget > 0.01:
            violations.append(
                f"Total allocation ${total_allocated:,.0f} "
                f"does not match budget ${total_budget:,.0f}"
            )
        
        # Check channel bounds
        budget_config = self.config['optimization']['budget']
        channel_bounds_config = budget_config.get('channel_bounds', {})
        
        for channel, spend in allocation.items():
            if channel not in channels:
                violations.append(f"Unknown channel: {channel}")
                continue
            
            channel_bound = channel_bounds_config.get(channel, {'min': 0.0, 'max': 1.0})
            
            min_spend = total_budget * channel_bound.get('min', 0.0)
            max_spend = total_budget * channel_bound.get('max', 1.0)
            
            if spend < min_spend:
                violations.append(
                    f"{channel}: ${spend:,.0f} below minimum ${min_spend:,.0f}"
                )
            
            if spend > max_spend:
                violations.append(
                    f"{channel}: ${spend:,.0f} above maximum ${max_spend:,.0f}"
                )
        
        is_valid = len(violations) == 0
        
        return is_valid, violations
