"""
Backtesting Module

Backtesting utilities for validating MMM model performance.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from sklearn.metrics import mean_absolute_percentage_error, r2_score
import logging


class Backtester:
    """Backtest MMM models against historical data."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def time_series_backtest(
        self,
        model,
        X: np.ndarray,
        y: np.ndarray,
        n_splits: int = 5
    ) -> Dict:
        """
        Perform time series backtesting.
        
        Args:
            model: Trained model
            X: Feature matrix
            y: Target vector
            n_splits: Number of backtesting windows
            
        Returns:
            Dictionary of backtesting metrics
        """
        from sklearn.model_selection import TimeSeriesSplit
        
        tscv = TimeSeriesSplit(n_splits=n_splits)
        
        metrics = {
            'fold_metrics': [],
            'avg_r2': 0.0,
            'avg_mape': 0.0
        }
        
        for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            
            # Train model on this fold
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            r2 = r2_score(y_test, y_pred)
            mape = mean_absolute_percentage_error(y_test, y_pred)
            
            fold_metrics = {
                'fold': fold + 1,
                'r2': float(r2),
                'mape': float(mape),
                'train_size': len(train_idx),
                'test_size': len(test_idx)
            }
            
            metrics['fold_metrics'].append(fold_metrics)
            
            self.logger.info(f"Fold {fold+1}: R²={r2:.3f}, MAPE={mape:.3f}")
        
        # Calculate averages
        metrics['avg_r2'] = np.mean([m['r2'] for m in metrics['fold_metrics']])
        metrics['avg_mape'] = np.mean([m['mape'] for m in metrics['fold_metrics']])
        
        return metrics
    
    def holdout_validation(
        self,
        model,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Dict:
        """
        Perform holdout validation.
        
        Args:
            model: Model to validate
            X_train: Training features
            y_train: Training target
            X_test: Test features
            y_test: Test target
            
        Returns:
            Validation metrics
        """
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        return {
            'r2': float(r2_score(y_test, y_pred)),
            'mape': float(mean_absolute_percentage_error(y_test, y_pred)),
            'predictions': y_pred.tolist(),
            'actuals': y_test.tolist()
        }
