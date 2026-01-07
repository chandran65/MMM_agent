"""
Segmentation Tools

Feature engineering and clustering utilities for segmentation.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Any
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import logging


class SegmentationTools:
    """
    Tools for feature engineering and clustering.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize segmentation tools.
        
        Args:
            config: Segmentation configuration dictionary
        """
        self.config = config
        self.scaler = None
        self.logger = logging.getLogger(__name__)
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer features for clustering.
        
        Args:
            df: Raw input dataframe
            
        Returns:
            DataFrame with engineered features
        """
        features_config = self.config['segmentation']['features']
        features = pd.DataFrame()
        
        # Identify columns from mapping or defaults
        mapping = self.config.get('variable_mapping', {})
        
        # Determine sales column
        sales_col = 'total_sales' # Default
        if 'output_variable' in mapping and 'column' in mapping['output_variable']:
            sales_col = mapping['output_variable']['column']
        elif 'total_sales' in df.columns:
            sales_col = 'total_sales'
        elif 'sales' in df.columns:
            sales_col = 'sales'
            
        # Determine volume column
        # Check if volume is in input_variables or just try defaults
        volume_col = 'total_volume'
        # Could check mapping here if we standardized a volume input key
        if 'total_volume' in df.columns:
            volume_col = 'total_volume'
        elif 'volume' in df.columns:
            volume_col = 'volume'
        
        # Total sales (assumed to exist)
        if 'total_sales' in features_config:
            features['total_sales'] = df[sales_col]
        
        # Total volume
        if 'total_volume' in features_config:
            features['total_volume'] = df.get(volume_col, 0)
        
        # Average price (sales / volume)
        if 'avg_price' in features_config:
            features['avg_price'] = np.where(
                features.get('total_volume', 1) > 0,
                features.get('total_sales', 0) / features.get('total_volume', 1),
                0
            )
        
        # Sales velocity (growth metric if time series data available)
        if 'sales_velocity' in features_config:
            if 'date' in df.columns:
                df_sorted = df.sort_values('date')
                features['sales_velocity'] = df_sorted[sales_col].pct_change().fillna(0)
            else:
                features['sales_velocity'] = 0
        
        # Volatility (standard deviation of sales)
        if 'volatility' in features_config:
            if 'date' in df.columns and 'sub_category' in df.columns:
                volatility = df.groupby('sub_category')[sales_col].std().fillna(0)
                features['volatility'] = df['sub_category'].map(volatility).fillna(0)
            else:
                features['volatility'] = 0
        
        # Handle missing values
        features = features.fillna(0)
        
        # Scale features
        scaling_method = self.config['segmentation']['scaling']['method']
        if scaling_method == 'standard':
            self.scaler = StandardScaler()
            features_scaled = pd.DataFrame(
                self.scaler.fit_transform(features),
                columns=features.columns,
                index=features.index
            )
            return features_scaled
        
        return features
    
    def cluster_segments(self, features: pd.DataFrame) -> Tuple[np.ndarray, Any]:
        """
        Perform clustering on features.
        
        Args:
            features: Engineered features dataframe
            
        Returns:
            Tuple of (cluster labels, fitted model)
        """
        method = self.config['segmentation']['method']
        n_clusters = self.config['segmentation']['n_clusters']
        random_state = self.config['segmentation']['random_state']
        
        if method == 'kmeans':
            model = KMeans(
                n_clusters=n_clusters,
                random_state=random_state,
                n_init=10
            )
            labels = model.fit_predict(features)
            
            self.logger.info(f"KMeans clustering completed with {n_clusters} clusters")
            
            # Visualize if output path is configured
            viz_path = self.config['segmentation']['output'].get('visualization_file')
            if viz_path:
                self._visualize_segments(features, labels, viz_path)
            
            return labels, model
        
        else:
            raise ValueError(f"Unsupported clustering method: {method}")
    
    def calculate_segment_stats(
        self,
        df: pd.DataFrame,
        labels: np.ndarray
    ) -> Dict:
        """
        Calculate statistics for each segment.
        
        Args:
            df: Original dataframe
            labels: Cluster labels
            
        Returns:
            Dictionary of segment statistics
        """
        df_with_labels = df.copy()
        df_with_labels['segment'] = labels
        
        stats = {}
        
        # Identify columns from mapping or defaults
        mapping = self.config.get('variable_mapping', {})
        
        sales_col = 'total_sales'
        if 'output_variable' in mapping and 'column' in mapping['output_variable']:
            sales_col = mapping['output_variable']['column']
        elif 'total_sales' in df.columns:
            sales_col = 'total_sales'
        elif 'sales' in df.columns:
            sales_col = 'sales'

        volume_col = 'total_volume'
        if 'total_volume' in df.columns:
            volume_col = 'total_volume'
        elif 'volume' in df.columns:
            volume_col = 'volume'
        
        for segment_id in np.unique(labels):
            segment_data = df_with_labels[df_with_labels['segment'] == segment_id]
            
            segment_name = self.config['segmentation']['segment_labels'].get(
                segment_id, f"Segment_{segment_id}"
            )
            
            stats[segment_name] = {
                'count': int(len(segment_data)),
                'total_sales': float(segment_data[sales_col].sum()),
                'total_volume': float(segment_data.get(volume_col, pd.Series([0])).sum()),
                'avg_sales': float(segment_data[sales_col].mean()),
                'avg_volume': float(segment_data.get(volume_col, pd.Series([0])).mean()),
            }
        
        return stats
    
    def _visualize_segments(
        self,
        features: pd.DataFrame,
        labels: np.ndarray,
        output_path: str
    ) -> None:
        """
        Create visualization of segments.
        
        Args:
            features: Feature dataframe
            labels: Cluster labels
            output_path: Path to save visualization
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        plt.figure(figsize=(12, 8))
        
        # Use first two features for 2D visualization
        if features.shape[1] >= 2:
            x_col = features.columns[0]
            y_col = features.columns[1]
            
            scatter = plt.scatter(
                features[x_col],
                features[y_col],
                c=labels,
                cmap='viridis',
                alpha=0.6,
                edgecolors='k'
            )
            
            plt.xlabel(x_col)
            plt.ylabel(y_col)
            plt.title('Segmentation Results')
            plt.colorbar(scatter, label='Segment')
            
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Saved visualization to {output_path}")
