"""
Segmentation Rules

Validation rules and business logic for segmentation.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import logging


class SegmentationRules:
    """
    Business rules and validation logic for segmentation.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize segmentation rules.
        
        Args:
            config: Segmentation configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def validate_input_data(self, df: pd.DataFrame) -> None:
        """
        Validate that input data meets requirements.
        
        Args:
            df: Input dataframe
            
        Raises:
            ValueError: If data does not meet requirements
        """
        required_columns = []
        
        # Check for sales column
        if 'total_sales' not in df.columns and 'sales' not in df.columns:
            required_columns.append('total_sales') # Will trigger error
            
        # Volume is optional or can be 'volume'
        # if 'total_volume' not in df.columns and 'volume' not in df.columns:
        #     required_columns.append('total_volume')
        
        # Check for required columns
        if required_columns:
            missing_cols = set(required_columns) - set(df.columns)
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}. Data must have 'sales' or 'total_sales'.")
        
        # Check for minimum samples
        min_samples = self.config['segmentation'].get('min_samples_per_segment', 10)
        if len(df) < min_samples * 2:
            raise ValueError(
                f"Insufficient data: need at least {min_samples * 2} samples, got {len(df)}"
            )
        
        # Identify columns to validate
        validation_cols = []
        if 'total_sales' in df.columns: validation_cols.append('total_sales')
        elif 'sales' in df.columns: validation_cols.append('sales')
        
        if 'total_volume' in df.columns: validation_cols.append('total_volume')
        elif 'volume' in df.columns: validation_cols.append('volume')

        # Check for missing values
        if df[validation_cols].isnull().any().any():
            self.logger.warning("Input data contains missing values - will be handled")
        
        # Check for negative values
        if (df[validation_cols] < 0).any().any():
            raise ValueError("Input data contains negative values in sales/volume columns")
        
        self.logger.info("Input data validation passed")
    
    def validate_segmentation_quality(
        self,
        features: pd.DataFrame,
        labels: np.ndarray,
        model: Any
    ) -> Dict[str, float]:
        """
        Validate the quality of segmentation.
        
        Args:
            features: Feature dataframe used for clustering
            labels: Cluster labels
            model: Fitted clustering model
            
        Returns:
            Dictionary of quality metrics
        """
        from sklearn.metrics import silhouette_score
        
        metrics = {}
        
        # Calculate silhouette score
        if len(np.unique(labels)) > 1:
            silhouette = silhouette_score(features, labels)
            metrics['silhouette_score'] = float(silhouette)
            
            # Check against threshold
            min_silhouette = self.config['segmentation']['validation'].get(
                'min_silhouette_score', 0.3
            )
            if silhouette < min_silhouette:
                self.logger.warning(
                    f"Silhouette score {silhouette:.3f} below threshold {min_silhouette}"
                )
        
        # Calculate inertia (for KMeans)
        if hasattr(model, 'inertia_'):
            metrics['inertia'] = float(model.inertia_)
        
        # Check segment sizes
        unique, counts = np.unique(labels, return_counts=True)
        segment_sizes = {int(k): int(v) for k, v in zip(unique, counts)}
        metrics['segment_sizes'] = segment_sizes
        
        min_samples = self.config['segmentation'].get('min_samples_per_segment', 10)
        for seg_id, count in segment_sizes.items():
            if count < min_samples:
                self.logger.warning(
                    f"Segment {seg_id} has only {count} samples (min: {min_samples})"
                )
        
        self.logger.info(f"Segmentation quality metrics: {metrics}")
        
        return metrics
    
    def enforce_business_constraints(self, segments: pd.DataFrame) -> pd.DataFrame:
        """
        Apply business logic constraints to segments.
        
        Args:
            segments: Segment mappings dataframe
            
        Returns:
            Constrained segment mappings
        """
        # Example: Ensure certain categories are in specific segments
        # This would be configured based on business rules
        
        # For now, return as-is (extendable for future rules)
        return segments
