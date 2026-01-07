"""
Optimization Solver

Implements constrained optimization using scipy.
"""

import numpy as np
from scipy.optimize import minimize
from typing import Dict, List, Tuple, Callable
import logging


class OptimizationSolver:
    """Solve constrained optimization problems for budget allocation."""
    
    def __init__(self, config: Dict):
        """
        Initialize optimization solver.
        
        Args:
            config: Optimization configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def optimize(
        self,
        response_curves: Dict,
        total_budget: float,
        bounds: List[Tuple],
        constraints: List[Dict],
        current_spend: Dict[str, float]
    ) -> Dict:
        """
        Optimize budget allocation to maximize response.
        
        Args:
            response_curves: Response curves for each channel
            total_budget: Total budget to allocate
            bounds: Bounds for each channel
            constraints: List of constraint dictionaries
            current_spend: Current spend by channel
            
        Returns:
            Dictionary with optimization results
        """
        channels = list(response_curves.keys())
        n_channels = len(channels)
        
        # Initial guess (equal allocation or current spend)
        x0 = self._get_initial_guess(channels, total_budget, current_spend)
        
        # Define objective function (negative because we minimize)
        def objective(spend_array):
            return -self._calculate_total_response(spend_array, channels, response_curves)
        
        # Run optimization
        solver_config = self.config['optimization']['solver']
        method = solver_config.get('method', 'SLSQP')
        maxiter = solver_config.get('maxiter', 1000)
        
        self.logger.info(f"Running optimization with {method} solver")
        
        # Multiple restarts for global optimization
        n_restarts = solver_config.get('n_restarts', 5)
        best_result = None
        best_value = float('inf')
        
        for restart in range(n_restarts):
            if restart > 0:
                # Random perturbation for restart
                x0_restart = x0 * (1 + np.random.uniform(-0.2, 0.2, n_channels))
                x0_restart = np.clip(x0_restart, [b[0] for b in bounds], [b[1] for b in bounds])
            else:
                x0_restart = x0
            
            result = minimize(
                objective,
                x0_restart,
                method=method,
                bounds=bounds,
                constraints=constraints,
                options={'maxiter': maxiter, 'ftol': 1e-6}
            )
            
            if result.fun < best_value:
                best_value = result.fun
                best_result = result
        
        if not best_result.success:
            self.logger.warning(f"Optimization did not converge: {best_result.message}")
        
        # Extract optimal spend
        optimal_spend_array = best_result.x
        optimal_spend = {
            channels[i]: float(optimal_spend_array[i])
            for i in range(n_channels)
        }
        
        # Calculate metrics
        expected_sales = self._calculate_total_response(
            optimal_spend_array, channels, response_curves
        )
        
        current_sales = self._calculate_total_response(
            np.array([current_spend.get(ch, 0) for ch in channels]),
            channels,
            response_curves
        )
        
        expected_lift = (expected_sales - current_sales) / current_sales if current_sales > 0 else 0
        
        # Calculate spend changes
        spend_changes = {
            channel: (optimal_spend[channel] - current_spend.get(channel, 0)) / current_spend.get(channel, 1)
            for channel in channels
        }
        
        # Calculate channel responses
        channel_responses = {
            channels[i]: self._get_response_for_spend(
                optimal_spend_array[i],
                response_curves[channels[i]]
            )
            for i in range(n_channels)
        }
        
        return {
            'optimal_spend': optimal_spend,
            'current_spend': current_spend,
            'total_budget': float(total_budget),
            'expected_sales': float(expected_sales),
            'current_sales': float(current_sales),
            'expected_lift': float(expected_lift),
            'spend_changes': spend_changes,
            'channel_responses': channel_responses,
            'overall_roi': float(expected_sales / total_budget) if total_budget > 0 else 0,
            'optimization_status': best_result.message,
            'iterations': best_result.nit
        }
    
    def _get_initial_guess(
        self,
        channels: List[str],
        total_budget: float,
        current_spend: Dict[str, float]
    ) -> np.ndarray:
        """
        Get initial guess for optimization.
        
        Args:
            channels: List of channel names
            total_budget: Total budget
            current_spend: Current spend by channel
            
        Returns:
            Initial spend array
        """
        current_total = sum(current_spend.values())
        
        if current_total > 0 and abs(current_total - total_budget) / total_budget < 0.1:
            # Use current spend if close to budget
            return np.array([current_spend.get(ch, 0) for ch in channels])
        else:
            # Equal allocation
            return np.ones(len(channels)) * (total_budget / len(channels))
    
    def _calculate_total_response(
        self,
        spend_array: np.ndarray,
        channels: List[str],
        response_curves: Dict
    ) -> float:
        """
        Calculate total response for given spend allocation.
        
        Args:
            spend_array: Array of spend values
            channels: List of channel names
            response_curves: Response curves dictionary
            
        Returns:
            Total response value
        """
        total_response = 0.0
        
        for i, channel in enumerate(channels):
            spend = spend_array[i]
            response = self._get_response_for_spend(spend, response_curves[channel])
            total_response += response
        
        return total_response
    
    def _get_response_for_spend(
        self,
        spend: float,
        curve_data: Dict
    ) -> float:
        """
        Get response for a given spend using interpolation.
        
        Args:
            spend: Spend value
            curve_data: Response curve data
            
        Returns:
            Response value
        """
        spend_points = np.array(curve_data['spend'])
        response_points = np.array(curve_data['response'])
        
        # Linear interpolation
        response = np.interp(spend, spend_points, response_points)
        
        return float(response)
