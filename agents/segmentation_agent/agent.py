"""
Segmentation Agent

Responsible for grouping sub-categories based on sales and volume data.
Implements clustering logic to create segments for downstream modeling.
"""

import pandas as pd
import numpy as np
import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
import logging

from .rules import SegmentationRules
from .tools import SegmentationTools


class SegmentationAgent:
    """
    Agent responsible for segmenting sub-categories into meaningful groups.
    
    This agent:
    - Loads raw sales and volume data
    - Applies feature engineering for clustering
    - Performs clustering using configurable methods
    - Validates segment quality
    - Persists segment mappings and statistics
    """
    
    def __init__(self, config_path: str = "config/segmentation.yaml", mapping_path: str = "config/variable_mapping.yaml"):
        """
        Initialize the Segmentation Agent.
        
        Args:
            config_path: Path to segmentation configuration file
            mapping_path: Path to variable mapping configuration file
        """
        self.config = self._load_config(config_path)
        
        # Load variable mapping if exists
        mapping_file = Path(mapping_path)
        if mapping_file.exists():
            with open(mapping_file, 'r') as f:
                mapping_config = yaml.safe_load(f)
                if mapping_config:
                    self.config['variable_mapping'] = mapping_config.get('variable_mapping', {})
        
        self.rules = SegmentationRules(self.config)
        self.tools = SegmentationTools(self.config)
        self.logger = logging.getLogger(__name__)
        
        self.segment_mappings = None
        self.segment_stats = None
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def execute(self, input_data_path: str) -> Dict:
        """
        Execute the segmentation workflow.
        
        Args:
            input_data_path: Path to input data file (CSV or parquet)
            
        Returns:
            Dictionary containing execution results and artifact paths
        """
        self.logger.info("Starting Segmentation Agent execution")
        
        # Step 1: Load data
        df = self._load_data(input_data_path)
        self.logger.info(f"Loaded data with {len(df)} rows")
        
        # Step 2: Validate data quality
        self.rules.validate_input_data(df)
        
        # Step 3: Feature engineering
        features_df = self.tools.engineer_features(df)
        self.logger.info(f"Engineered {features_df.shape[1]} features")
        
        # Step 4: Perform clustering
        segment_labels, cluster_model = self.tools.cluster_segments(features_df)
        
        # Step 5: Create segment mappings
        self.segment_mappings = self._create_segment_mappings(df, segment_labels)
        
        # Step 6: Calculate segment statistics
        self.segment_stats = self.tools.calculate_segment_stats(df, segment_labels)
        
        # Step 7: Validate segmentation quality
        quality_metrics = self.rules.validate_segmentation_quality(
            features_df, segment_labels, cluster_model
        )
        
        # Step 8: Persist outputs
        output_paths = self._persist_outputs()
        
        self.logger.info("Segmentation Agent execution completed")
        
        return {
            "status": "success",
            "n_segments": int(len(np.unique(segment_labels))),
            "quality_metrics": quality_metrics,
            "output_paths": output_paths,
            "segment_distribution": {int(k): int(v) for k, v in pd.Series(segment_labels).value_counts().items()}
        }
    
    def _load_data(self, data_path: str) -> pd.DataFrame:
        """Load input data from file."""
        path = Path(data_path)
        
        if path.suffix == '.csv':
            return pd.read_csv(data_path, sep=None, engine='python')
        elif path.suffix == '.parquet':
            return pd.read_parquet(data_path)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
    
    def _create_segment_mappings(
        self, 
        df: pd.DataFrame, 
        segment_labels: np.ndarray
    ) -> pd.DataFrame:
        """
        Create mapping from sub-categories to segments.
        
        Args:
            df: Original dataframe
            segment_labels: Cluster labels from clustering algorithm
            
        Returns:
            DataFrame with sub_category to segment mapping
        """
        segment_config = self.config['segmentation']['segment_labels']
        
        # Assume df has a 'sub_category' column
        if 'sub_category' not in df.columns:
            # Use index as sub_category identifier
            df['sub_category'] = df.index
        
        mapping_df = pd.DataFrame({
            'sub_category': df['sub_category'].values,
            'segment_id': segment_labels,
            'segment_name': [segment_config.get(label, f"Segment_{label}") 
                           for label in segment_labels]
        })
        
        return mapping_df
    
    def _persist_outputs(self) -> Dict[str, str]:
        """Save segment mappings and statistics to disk."""
        output_config = self.config['segmentation']['output']
        
        # Save segment mappings
        mapping_path = output_config['segment_mapping_file']
        Path(mapping_path).parent.mkdir(parents=True, exist_ok=True)
        self.segment_mappings.to_csv(mapping_path, index=False)
        
        # Save segment statistics
        stats_path = output_config['segment_stats_file']
        Path(stats_path).parent.mkdir(parents=True, exist_ok=True)
        with open(stats_path, 'w') as f:
            json.dump(self.segment_stats, f, indent=2)
        
        # Visualizations are saved by tools
        
        return {
            "segment_mappings": mapping_path,
            "segment_statistics": stats_path,
            "visualization": output_config.get('visualization_file')
        }
    
    def get_segment_for_category(self, sub_category: str) -> str:
        """
        Get segment name for a given sub-category.
        
        Args:
            sub_category: Sub-category identifier
            
        Returns:
            Segment name
        """
        if self.segment_mappings is None:
            raise ValueError("Segmentation has not been executed yet")
        
        row = self.segment_mappings[
            self.segment_mappings['sub_category'] == sub_category
        ]
        
        if len(row) == 0:
            raise ValueError(f"Sub-category '{sub_category}' not found in mappings")
        
        return row.iloc[0]['segment_name']
