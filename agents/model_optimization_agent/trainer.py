"""
Model Trainer

Trains MMM/MMX regression models and calculates performance metrics.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit
import logging


class ModelTrainer:
    """Train and evaluate MMM models."""
    
    def __init__(self, config: Dict, global_config: Dict):
        """
        Initialize model trainer.
        
        Args:
            config: Priors configuration
            global_config: Global configuration
        """
        self.config = config
        self.global_config = global_config
        self.logger = logging.getLogger(__name__)
    
    def train_model(
        self,
        transformed_df: pd.DataFrame,
        baseline_df: pd.DataFrame,
        channels: List[str]
    ) -> Tuple[object, Dict]:
        """
        Train MMM regression model.
        
        Args:
            transformed_df: DataFrame with transformed features
            baseline_df: DataFrame with baseline estimates
            channels: List of channel names
            
        Returns:
            Tuple of (trained model, metrics dictionary)
        """
        self.logger.info("Preparing training data")
        
        # Prepare features (transformed channel spends)
        feature_cols = [f'{channel}_transformed' for channel in channels 
                       if f'{channel}_transformed' in transformed_df.columns]
        
        X = transformed_df[feature_cols].fillna(0).values
        
        # Prepare target (incremental sales, i.e., sales minus baseline)
        sales_col = 'sales' if 'sales' in transformed_df.columns else 'total_sales'
        y_total = transformed_df[sales_col].values
        
        # Subtract baseline to get incremental sales from marketing
        baseline_values = baseline_df['baseline'].values[:len(y_total)]
        y = y_total - baseline_values
        
        # Split data for validation
        split_ratio = self.global_config['modeling'].get('train_test_split', 0.8)
        split_idx = int(len(X) * split_ratio)
        
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        self.logger.info(f"Training set: {len(X_train)}, Test set: {len(X_test)}")
        
        # Train model
        model_type = self.global_config['modeling'].get('model_type', 'ridge')
        
        if model_type == 'bayesian':
            from sklearn.linear_model import BayesianRidge
            self.logger.info("Training Bayesian Ridge Regression model...")
            model = BayesianRidge(
                n_iter=300,
                tol=1e-3,
                alpha_1=1e-6, alpha_2=1e-6,  # Hyperparameters for Gamma prior on weights
                lambda_1=1e-6, lambda_2=1e-6
            )
        else:
            # Default to Ridge
            reg_config = self.config.get('regularization', {})
            alpha = reg_config.get('ridge_alpha', 0.1)
            model = Ridge(alpha=alpha, positive=True)

        model.fit(X_train, y_train)
        
        self.logger.info("Model training completed")
        
        # Calculate metrics
        metrics = self._calculate_metrics(model, X_train, y_train, X_test, y_test, feature_cols)
        
        return model, metrics
    
    def _calculate_metrics(
        self,
        model: object,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        feature_names: List[str]
    ) -> Dict:
        """
        Calculate model performance metrics.
        
        Args:
            model: Trained model
            X_train: Training features
            y_train: Training target
            X_test: Test features
            y_test: Test target
            feature_names: List of feature names
            
        Returns:
            Dictionary of metrics
        """
        # Predictions
        y_train_pred = model.predict(X_train)
        y_test_pred = model.predict(X_test)
        
        # R-squared
        r2_train = r2_score(y_train, y_train_pred)
        r2_test = r2_score(y_test, y_test_pred)
        
        # Adjusted R-squared
        n_train = len(y_train)
        p = X_train.shape[1]
        adj_r2_train = 1 - (1 - r2_train) * (n_train - 1) / (n_train - p - 1)
        
        # MAE and RMSE
        mae_train = mean_absolute_error(y_train, y_train_pred)
        mae_test = mean_absolute_error(y_test, y_test_pred)
        
        rmse_train = np.sqrt(mean_squared_error(y_train, y_train_pred))
        rmse_test = np.sqrt(mean_squared_error(y_test, y_test_pred))
        
        # MAPE (Mean Absolute Percentage Error)
        mape_train = np.mean(np.abs((y_train - y_train_pred) / (y_train + 1e-10))) * 100
        mape_test = np.mean(np.abs((y_test - y_test_pred) / (y_test + 1e-10))) * 100
        
        # Coefficients
        coefficients = {
            feature_names[i]: float(model.coef_[i])
            for i in range(len(feature_names))
        }
        
        metrics = {
            'r_squared': float(r2_test),
            'r_squared_train': float(r2_train),
            'adjusted_r_squared': float(adj_r2_train),
            'mae': float(mae_test),
            'mae_train': float(mae_train),
            'rmse': float(rmse_test),
            'rmse_train': float(rmse_train),
            'mape': float(mape_test),
            'mape_train': float(mape_train),
            'coefficients': coefficients,
            'intercept': float(model.intercept_) if hasattr(model, 'intercept_') else 0.0
        }
        
        self.logger.info(f"Model R²: {r2_test:.3f}, MAE: {mae_test:.2f}, MAPE: {mape_test:.2f}%")
        
        return metrics
    
    def cross_validate(
        self,
        X: np.ndarray,
        y: np.ndarray,
        n_splits: int = 5
    ) -> Dict:
        """
        Perform time series cross-validation.
        
        Args:
            X: Feature matrix
            y: Target vector
            n_splits: Number of CV splits
            
        Returns:
            Dictionary of CV metrics
        """
        tscv = TimeSeriesSplit(n_splits=n_splits)
        
        r2_scores = []
        mae_scores = []
        
        reg_config = self.config.get('regularization', {})
        alpha = reg_config.get('ridge_alpha', 0.1)
        
        for train_idx, val_idx in tscv.split(X):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            
            model = Ridge(alpha=alpha, positive=True)
            model.fit(X_train, y_train)
            
            y_pred = model.predict(X_val)
            
            r2_scores.append(r2_score(y_val, y_pred))
            mae_scores.append(mean_absolute_error(y_val, y_pred))
        
        cv_metrics = {
            'cv_r2_mean': float(np.mean(r2_scores)),
            'cv_r2_std': float(np.std(r2_scores)),
            'cv_mae_mean': float(np.mean(mae_scores)),
            'cv_mae_std': float(np.std(mae_scores))
        }
        
        return cv_metrics
