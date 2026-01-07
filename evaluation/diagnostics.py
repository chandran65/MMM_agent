"""
Model Diagnostics

Diagnostic tools for evaluating MMM model quality.
"""

import pandas as pd
import numpy as np
from typing import Dict
from scipy import stats
import logging


class ModelDiagnostics:
    """Diagnostic tools for MMM model validation."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def check_residuals(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> Dict:
        """
        Check residual properties.
        
        Args:
            y_true: Actual values
            y_pred: Predicted values
            
        Returns:
            Dictionary of residual diagnostics
        """
        residuals = y_true - y_pred
        
        # Normality test
        _, normality_p = stats.normaltest(residuals)
        
        # Autocorrelation (Durbin-Watson)
        durbin_watson = self._durbin_watson_statistic(residuals)
        
        # Heteroscedasticity test (simple variance comparison)
        n = len(residuals)
        first_half_var = np.var(residuals[:n//2])
        second_half_var = np.var(residuals[n//2:])
        
        diagnostics = {
            'mean_residual': float(np.mean(residuals)),
            'std_residual': float(np.std(residuals)),
            'normality_p_value': float(normality_p),
            'is_normal': normality_p > 0.05,
            'durbin_watson': float(durbin_watson),
            'heteroscedasticity_ratio': float(second_half_var / first_half_var if first_half_var > 0 else 0)
        }
        
        return diagnostics
    
    def check_multicollinearity(
        self,
        X: np.ndarray,
        feature_names: list
    ) -> Dict:
        """
        Check for multicollinearity using VIF.
        
        Args:
            X: Feature matrix
            feature_names: List of feature names
            
        Returns:
            Dictionary of VIF values
        """
        from sklearn.linear_model import LinearRegression
        
        vif_values = {}
        
        for i, feature in enumerate(feature_names):
            # VIF = 1 / (1 - R²)
            # where R² is from regressing feature i on all other features
            
            other_features_idx = [j for j in range(X.shape[1]) if j != i]
            
            if len(other_features_idx) == 0:
                vif_values[feature] = 1.0
                continue
            
            X_others = X[:, other_features_idx]
            y_feature = X[:, i]
            
            model = LinearRegression()
            model.fit(X_others, y_feature)
            r2 = model.score(X_others, y_feature)
            
            vif = 1 / (1 - r2) if r2 < 0.99 else 999
            vif_values[feature] = float(vif)
        
        return vif_values
    
    def _durbin_watson_statistic(self, residuals: np.ndarray) -> float:
        """
        Calculate Durbin-Watson statistic.
        
        Args:
            residuals: Array of residuals
            
        Returns:
            Durbin-Watson statistic (ideally around 2.0)
        """
        diff_resid = np.diff(residuals)
        dw = np.sum(diff_resid**2) / np.sum(residuals**2)
        return float(dw)
    
    def generate_diagnostic_report(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        X: np.ndarray,
        feature_names: list
    ) -> Dict:
        """
        Generate complete diagnostic report.
        
        Args:
            y_true: Actual values
            y_pred: Predicted values
            X: Feature matrix
            feature_names: List of feature names
            
        Returns:
            Complete diagnostic report
        """
        report = {
            'residuals': self.check_residuals(y_true, y_pred),
            'multicollinearity': self.check_multicollinearity(X, feature_names)
        }
        
        # Flag issues
        issues = []
        
        if not report['residuals']['is_normal']:
            issues.append("Residuals not normally distributed")
        
        if abs(report['residuals']['durbin_watson'] - 2.0) > 0.5:
            issues.append("Possible autocorrelation in residuals")
        
        high_vif = [f for f, v in report['multicollinearity'].items() if v > 10]
        if high_vif:
            issues.append(f"High multicollinearity in: {', '.join(high_vif)}")
        
        report['issues'] = issues
        report['passes_diagnostics'] = len(issues) == 0
        
        return report
