"""
Trend Scanner Agent

Detects year-over-year trends, seasonality, anomalies, and major event effects.
Provides flagged periods and event metadata for baseline estimation.
"""

import pandas as pd
import numpy as np
import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import logging

from .detectors import (
    TrendDetector,
    SeasonalityDetector,
    AnomalyDetector,
    EventDetector
)


class TrendScannerAgent:
    """
    Agent responsible for scanning time series data for trends and anomalies.
    
    This agent:
    - Detects YoY (Year-over-Year) trends
    - Identifies seasonality patterns
    - Flags anomalous periods
    - Maps major events that impact sales
    """
    
    def __init__(self, config_path: str = "config/global.yaml"):
        """
        Initialize the Trend Scanner Agent.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        
        # Load variable mapping if exists
        mapping_path = "config/variable_mapping.yaml"
        self.mapping = {}
        if Path(mapping_path).exists():
             with open(mapping_path, 'r') as f:
                mapping_config = yaml.safe_load(f)
                if mapping_config:
                    self.mapping = mapping_config.get('variable_mapping', {})
                    
        self.logger = logging.getLogger(__name__)
        
        # Initialize detectors
        self.trend_detector = TrendDetector()
        self.seasonality_detector = SeasonalityDetector()
        self.anomaly_detector = AnomalyDetector()
        self.event_detector = EventDetector()
        
        self.trend_results = None
        self.flagged_periods = []
        self.event_metadata = {}
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def execute(self, input_data_path: str, events_path: str = None) -> Dict:
        """
        Execute the trend scanning workflow.
        
        Args:
            input_data_path: Path to time series data (must have date column)
            events_path: Optional path to known events data
            
        Returns:
            Dictionary containing execution results and artifact paths
        """
        self.logger.info("Starting Trend Scanner Agent execution")
        
        # Step 1: Load data
        df = self._load_data(input_data_path)
        self.logger.info(f"Loaded time series data with {len(df)} periods")
        
        # Step 2: Validate time series data
        self._validate_time_series(df)
        
        # Step 3: Detect YoY trends
        yoy_trends = self.trend_detector.detect_yoy_trends(df)
        self.logger.info(f"Detected {len(yoy_trends)} YoY trend changes")
        
        # Step 4: Detect seasonality
        seasonality_info = self.seasonality_detector.detect_seasonality(df)
        self.logger.info(f"Seasonality detected: {seasonality_info['has_seasonality']}")
        
        # Step 5: Detect anomalies
        anomalies = self.anomaly_detector.detect_anomalies(df)
        self.logger.info(f"Detected {len(anomalies)} anomalous periods")
        
        # Step 6: Detect event impacts
        if events_path:
            events_df = pd.read_csv(events_path)
            event_impacts = self.event_detector.detect_event_impacts(df, events_df)
        else:
            event_impacts = []
        self.logger.info(f"Detected {len(event_impacts)} event impacts")
        
        # Step 7: Consolidate flagged periods
        self.flagged_periods = self._consolidate_flagged_periods(
            yoy_trends, anomalies, event_impacts
        )
        
        # Step 8: Create event metadata
        self.event_metadata = self._create_event_metadata(
            seasonality_info, event_impacts
        )
        
        # Step 9: Persist outputs
        output_paths = self._persist_outputs(df)
        
        self.logger.info("Trend Scanner Agent execution completed")
        
        return {
            "status": "success",
            "n_flagged_periods": len(self.flagged_periods),
            "n_events": len(event_impacts),
            "has_seasonality": seasonality_info['has_seasonality'],
            "output_paths": output_paths
        }
    
    def _load_data(self, data_path: str) -> pd.DataFrame:
        """Load time series data from file."""
        df = pd.read_csv(data_path, sep=None, engine='python')
        
        # Ensure date column exists and is datetime
        date_col = self.mapping.get('date_column')
        
        if date_col and date_col in df.columns:
            df['date'] = pd.to_datetime(df[date_col])
        elif 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        elif 'week' in df.columns:
            df['date'] = pd.to_datetime(df['week'])
        else:
            raise ValueError(f"Data must have 'date' or 'week' column, or '{date_col}' as configured")
        
        return df.sort_values('date')
    
    def _validate_time_series(self, df: pd.DataFrame) -> None:
        """Validate that data is suitable for trend analysis."""
        # Validate that data is suitable for trend analysis.
        sales_col = 'total_sales'
        if 'output_variable' in self.mapping:
            sales_col = self.mapping['output_variable']['column']
            if sales_col not in df.columns:
                 # Fallback to loose check if mapped column not found (though this is risky)
                 if 'sales' not in df.columns and 'total_sales' not in df.columns:
                     raise ValueError(f"Data must have configured output column '{sales_col}'")
        
        if sales_col not in df.columns and 'sales' not in df.columns and 'total_sales' not in df.columns:
            raise ValueError("Data must have 'sales' or 'total_sales' column")
        
        # Check for sufficient history
        n_weeks = len(df)
        min_weeks = 52  # At least 1 year
        if n_weeks < min_weeks:
            raise ValueError(f"Need at least {min_weeks} weeks of data, got {n_weeks}")
        
        # Check for gaps in time series
        date_diff = df['date'].diff()
        expected_freq = pd.Timedelta(days=7)  # Weekly
        gaps = date_diff[date_diff > expected_freq * 1.5]
        
        if len(gaps) > 0:
            self.logger.warning(f"Found {len(gaps)} gaps in time series")
    
    def _consolidate_flagged_periods(
        self,
        yoy_trends: List[Dict],
        anomalies: List[Dict],
        event_impacts: List[Dict]
    ) -> List[Dict]:
        """
        Consolidate all flagged periods from different detectors.
        
        Args:
            yoy_trends: List of YoY trend changes
            anomalies: List of anomalous periods
            event_impacts: List of event impacts
            
        Returns:
            Consolidated list of flagged periods
        """
        flagged = []
        
        # Add trend changes
        for trend in yoy_trends:
            flagged.append({
                'date': pd.to_datetime(trend['date']),
                'type': 'trend_change',
                'description': trend['description'],
                'magnitude': trend.get('change_pct', 0)
            })
        
        # Add anomalies
        for anomaly in anomalies:
            flagged.append({
                'date': anomaly['date'],
                'type': 'anomaly',
                'description': 'Anomalous sales pattern',
                'magnitude': anomaly.get('deviation', 0)
            })
        
        # Add events
        for event in event_impacts:
            flagged.append({
                'date': event['date'],
                'type': 'event',
                'description': event['event_name'],
                'magnitude': event.get('impact', 0)
            })
        
        return sorted(flagged, key=lambda x: x['date'])
    
    def _create_event_metadata(
        self,
        seasonality_info: Dict,
        event_impacts: List[Dict]
    ) -> Dict:
        """
        Create structured metadata about events and patterns.
        
        Args:
            seasonality_info: Seasonality detection results
            event_impacts: Detected event impacts
            
        Returns:
            Event metadata dictionary
        """
        metadata = {
            'seasonality': seasonality_info,
            'events': event_impacts,
            'summary': {
                'has_strong_seasonality': seasonality_info.get('strength', 0) > 0.3,
                'n_major_events': len([e for e in event_impacts if abs(e.get('impact', 0)) > 0.1]),
                'requires_adjustment': len(event_impacts) > 0
            }
        }
        
        return metadata
    
    def _persist_outputs(self, df: pd.DataFrame) -> Dict[str, str]:
        """Save flagged periods and event metadata to disk."""
        output_dir = Path("data/processed")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save flagged periods
        flagged_path = output_dir / "flagged_periods.csv"
        pd.DataFrame(self.flagged_periods).to_csv(flagged_path, index=False)
        
        # Save event metadata
        metadata_path = output_dir / "event_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(self.event_metadata, f, indent=2, default=str)
        
        # Save trend visualization
        viz_path = Path("artifacts") / "trends_visualization.png"
        self.trend_detector.visualize_trends(df, viz_path)
        
        return {
            "flagged_periods": str(flagged_path),
            "event_metadata": str(metadata_path),
            "visualization": str(viz_path)
        }
    
    def get_adjustment_factors(self, date: pd.Timestamp) -> Dict[str, float]:
        """
        Get adjustment factors for a specific date.
        
        Args:
            date: Date to get adjustments for
            
        Returns:
            Dictionary of adjustment factors
        """
        adjustments = {
            'seasonality': 1.0,
            'event': 1.0,
            'trend': 1.0
        }
        
        # Apply seasonality adjustment
        seasonality = self.event_metadata.get('seasonality', {})
        if seasonality.get('has_seasonality'):
            # This would use actual seasonal decomposition
            pass
        
        # Apply event adjustment
        for event in self.event_metadata.get('events', []):
            if event['date'] == date:
                adjustments['event'] = 1.0 + event.get('impact', 0)
        
        return adjustments
