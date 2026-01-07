"""
Trend and Anomaly Detectors

Statistical methods for detecting trends, seasonality, anomalies, and events.
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from scipy import stats
from statsmodels.tsa.seasonal import seasonal_decompose
import matplotlib.pyplot as plt
from pathlib import Path
import logging


class TrendDetector:
    """Detect year-over-year trends and trend changes."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def detect_yoy_trends(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect year-over-year trend changes.
        
        Args:
            df: Time series dataframe with date and sales columns
            
        Returns:
            List of detected trend changes
        """
        sales_col = 'sales' if 'sales' in df.columns else 'total_sales'
        
        # Calculate YoY changes
        df = df.copy()
        df['year'] = df['date'].dt.year
        df['week'] = df['date'].dt.isocalendar().week
        
        trends = []
        
        for year in sorted(df['year'].unique())[1:]:
            current_year = df[df['year'] == year][sales_col].sum()
            previous_year = df[df['year'] == year - 1][sales_col].sum()
            
            if previous_year > 0:
                yoy_change = (current_year - previous_year) / previous_year
                
                if abs(yoy_change) > 0.1:  # 10% threshold
                    trends.append({
                        'date': f'{year}-01-01',
                        'description': f'YoY change of {yoy_change:.1%}',
                        'change_pct': float(yoy_change)
                    })
        
        return trends
    
    def visualize_trends(self, df: pd.DataFrame, output_path: Path) -> None:
        """
        Create visualization of trends.
        
        Args:
            df: Time series dataframe
            output_path: Path to save visualization
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        sales_col = 'sales' if 'sales' in df.columns else 'total_sales'
        
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        
        # Plot raw sales
        axes[0].plot(df['date'], df[sales_col], label='Sales', linewidth=1.5)
        axes[0].set_xlabel('Date')
        axes[0].set_ylabel('Sales')
        axes[0].set_title('Sales Time Series')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Plot rolling average
        rolling_mean = df[sales_col].rolling(window=4, center=True).mean()
        axes[1].plot(df['date'], rolling_mean, label='4-week Moving Average', 
                    color='orange', linewidth=2)
        axes[1].set_xlabel('Date')
        axes[1].set_ylabel('Sales (Moving Avg)')
        axes[1].set_title('Sales Trend (4-week Moving Average)')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()


class SeasonalityDetector:
    """Detect seasonal patterns in time series."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def detect_seasonality(self, df: pd.DataFrame) -> Dict:
        """
        Detect seasonality in the time series.
        
        Args:
            df: Time series dataframe
            
        Returns:
            Dictionary with seasonality information
        """
        sales_col = 'sales' if 'sales' in df.columns else 'total_sales'
        
        # Require at least 2 years of data for seasonal decomposition
        if len(df) < 104:  # 2 years of weekly data
            return {
                'has_seasonality': False,
                'reason': 'Insufficient data for seasonal decomposition'
            }
        
        try:
            # Perform seasonal decomposition
            decomposition = seasonal_decompose(
                df[sales_col],
                model='additive',
                period=52,  # Weekly data, yearly seasonality
                extrapolate_trend='freq'
            )
            
            # Calculate strength of seasonality
            seasonal_strength = (
                np.var(decomposition.seasonal) / 
                np.var(decomposition.seasonal + decomposition.resid)
            )
            
            return {
                'has_seasonality': seasonal_strength > 0.1,
                'strength': float(seasonal_strength),
                'period': 52,
                'seasonal_component': decomposition.seasonal.tolist()
            }
        
        except Exception as e:
            self.logger.warning(f"Seasonality detection failed: {e}")
            return {
                'has_seasonality': False,
                'reason': str(e)
            }


class AnomalyDetector:
    """Detect anomalous periods in time series."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def detect_anomalies(
        self,
        df: pd.DataFrame,
        threshold: float = 3.0
    ) -> List[Dict]:
        """
        Detect anomalies using statistical methods.
        
        Args:
            df: Time series dataframe
            threshold: Number of standard deviations for anomaly
            
        Returns:
            List of detected anomalies
        """
        sales_col = 'sales' if 'sales' in df.columns else 'total_sales'
        
        # Calculate z-scores
        sales = df[sales_col].values
        z_scores = np.abs(stats.zscore(sales))
        
        anomalies = []
        
        for idx, (date, z_score) in enumerate(zip(df['date'], z_scores)):
            if z_score > threshold:
                anomalies.append({
                    'date': date,
                    'sales': float(sales[idx]),
                    'deviation': float(z_score),
                    'type': 'spike' if sales[idx] > np.mean(sales) else 'drop'
                })
        
        return anomalies


class EventDetector:
    """Detect and quantify impact of known events."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def detect_event_impacts(
        self,
        sales_df: pd.DataFrame,
        events_df: pd.DataFrame
    ) -> List[Dict]:
        """
        Detect impact of known events on sales.
        
        Args:
            sales_df: Time series sales data
            events_df: Dataframe with events (must have 'event_date' and 'event_name')
            
        Returns:
            List of event impacts
        """
        if events_df is None or len(events_df) == 0:
            return []
        
        sales_col = 'sales' if 'sales' in sales_df.columns else 'total_sales'
        
        # Ensure date columns are datetime
        if 'event_date' in events_df.columns:
            events_df['event_date'] = pd.to_datetime(events_df['event_date'])
        else:
            return []
        
        impacts = []
        
        for _, event in events_df.iterrows():
            event_date = event['event_date']
            
            # Find sales around event date
            event_sales = sales_df[sales_df['date'] == event_date]
            
            if len(event_sales) > 0:
                # Calculate baseline (average of 4 weeks before)
                baseline_sales = sales_df[
                    (sales_df['date'] < event_date) &
                    (sales_df['date'] >= event_date - pd.Timedelta(weeks=4))
                ][sales_col].mean()
                
                actual_sales = event_sales[sales_col].values[0]
                
                if baseline_sales > 0:
                    impact = (actual_sales - baseline_sales) / baseline_sales
                    
                    impacts.append({
                        'date': event_date,
                        'event_name': event.get('event_name', 'Unknown Event'),
                        'impact': float(impact),
                        'baseline_sales': float(baseline_sales),
                        'actual_sales': float(actual_sales)
                    })
        
        return impacts
