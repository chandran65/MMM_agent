"""
Insight Agent

Generates executive-ready insights, narratives, and visualizations from MMX outputs.
"""

import pandas as pd
import numpy as np
import json
import yaml
from pathlib import Path
from typing import Dict, List
import logging

from .narratives import NarrativeGenerator
from .visuals import VisualizationEngine


class InsightAgent:
    """
    Agent responsible for generating stakeholder-ready insights.
    
    This agent:
    - Synthesizes insights from all previous agents
    - Generates executive narratives
    - Creates visualizations (charts, tables)
    - Produces Excel and PowerPoint ready outputs
    """
    
    def __init__(
        self,
        config_path: str = "config/global.yaml"
    ):
        """
        Initialize the Insight Agent.
        
        Args:
            config_path: Path to global configuration
        """
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
        
        self.narrative_generator = NarrativeGenerator()
        self.visualization_engine = VisualizationEngine()
        
        self.insights = None
        self.narratives = None
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def execute(
        self,
        contributions_path: str,
        optimization_path: str,
        model_metrics_path: str,
        response_curves_path: str = None
    ) -> Dict:
        """
        Execute the insight generation workflow.
        
        Args:
            contributions_path: Path to channel contributions CSV
            optimization_path: Path to optimization recommendations CSV
            model_metrics_path: Path to model metrics JSON
            response_curves_path: Optional path to response curves
            
        Returns:
            Dictionary containing execution results and artifact paths
        """
        self.logger.info("Starting Insight Agent execution")
        
        # Step 1: Load all artifacts
        contributions_df = pd.read_csv(contributions_path)
        optimization_df = pd.read_csv(optimization_path)
        
        with open(model_metrics_path, 'r') as f:
            model_metrics = json.load(f)
        
        response_curves = None
        if response_curves_path and Path(response_curves_path).exists():
            with open(response_curves_path, 'r') as f:
                response_curves = json.load(f)
        
        self.logger.info("Loaded all artifacts")
        
        # Step 2: Generate key insights
        self.insights = self._generate_insights(
            contributions_df,
            optimization_df,
            model_metrics,
            response_curves
        )
        self.logger.info(f"Generated {len(self.insights)} key insights")
        
        # Step 3: Generate narratives
        self.narratives = self.narrative_generator.generate_narratives(
            self.insights,
            contributions_df,
            optimization_df,
            model_metrics
        )
        self.logger.info("Generated executive narratives")
        
        # Step 4: Create visualizations
        visualization_paths = self.visualization_engine.create_visualizations(
            contributions_df,
            optimization_df,
            response_curves
        )
        self.logger.info(f"Created {len(visualization_paths)} visualizations")
        
        # Step 5: Create summary tables
        summary_tables = self._create_summary_tables(
            contributions_df,
            optimization_df
        )
        
        # Step 6: Persist outputs
        output_paths = self._persist_outputs(
            summary_tables,
            visualization_paths
        )
        
        self.logger.info("Insight Agent execution completed")
        
        return {
            "status": "success",
            "n_insights": len(self.insights),
            "n_narratives": len(self.narratives),
            "n_visualizations": len(visualization_paths),
            "output_paths": output_paths
        }
    
    def _generate_insights(
        self,
        contributions_df: pd.DataFrame,
        optimization_df: pd.DataFrame,
        model_metrics: Dict,
        response_curves: Dict = None
    ) -> List[Dict]:
        """
        Generate key insights from data.
        
        Args:
            contributions_df: Channel contributions dataframe
            optimization_df: Optimization results dataframe
            model_metrics: Model performance metrics
            response_curves: Response curves data
            
        Returns:
            List of insight dictionaries
        """
        insights = []
        
        # Insight 1: Model Performance
        insights.append({
            'category': 'model_performance',
            'title': 'Model Quality',
            'metric': f"R² = {model_metrics.get('r_squared', 0):.3f}",
            'description': f"Model explains {model_metrics.get('r_squared', 0)*100:.1f}% of sales variance",
            'quality': 'good' if model_metrics.get('r_squared', 0) > 0.7 else 'acceptable'
        })
        
        # Insight 2: Top Contributing Channel
        if not contributions_df.empty:
            top_channel = contributions_df.loc[
                contributions_df['contribution_pct'].idxmax()
            ]
            
            insights.append({
                'category': 'top_performer',
                'title': 'Highest Contributing Channel',
                'metric': top_channel['channel'],
                'value': f"{top_channel['contribution_pct']:.1f}%",
                'description': f"{top_channel['channel']} drives {top_channel['contribution_pct']:.1f}% of incremental sales"
            })
        
        # Insight 3: Optimization Opportunity
        base_scenario = optimization_df[optimization_df['scenario'] == 'base']
        if not base_scenario.empty:
            total_change = base_scenario['change_pct'].abs().sum()
            
            insights.append({
                'category': 'optimization',
                'title': 'Optimization Potential',
                'metric': f"{total_change:.1f}% total reallocation",
                'description': 'Recommended budget reallocation to maximize ROI'
            })
        
        # Insight 4: Over/Under Invested Channels
        if not base_scenario.empty:
            overinvested = base_scenario[base_scenario['change_pct'] < -0.10]
            underinvested = base_scenario[base_scenario['change_pct'] > 0.10]
            
            if not overinvested.empty:
                insights.append({
                    'category': 'overinvestment',
                    'title': 'Overinvested Channels',
                    'channels': overinvested['channel'].tolist(),
                    'description': f"Reduce spend in {', '.join(overinvested['channel'].tolist())}"
                })
            
            if not underinvested.empty:
                insights.append({
                    'category': 'underinvestment',
                    'title': 'Underinvested Channels',
                    'channels': underinvested['channel'].tolist(),
                    'description': f"Increase spend in {', '.join(underinvested['channel'].tolist())}"
                })
        
        # Insight 5: Saturation Analysis
        if response_curves:
            saturated_channels = []
            for channel, curve_data in response_curves.items():
                current_spend = curve_data.get('current_spend_avg', 0)
                optimal_point = curve_data.get('optimal_efficiency_point', 0)
                
                if current_spend > optimal_point * 1.5:
                    saturated_channels.append(channel)
            
            if saturated_channels:
                insights.append({
                    'category': 'saturation',
                    'title': 'Saturated Channels',
                    'channels': saturated_channels,
                    'description': f"{', '.join(saturated_channels)} operating beyond optimal efficiency"
                })
        
        return insights
    
    def _create_summary_tables(
        self,
        contributions_df: pd.DataFrame,
        optimization_df: pd.DataFrame
    ) -> Dict[str, pd.DataFrame]:
        """
        Create summary tables for Excel export.
        
        Args:
            contributions_df: Channel contributions
            optimization_df: Optimization results
            
        Returns:
            Dictionary of summary tables
        """
        tables = {}
        
        # Table 1: Channel Contribution Summary
        contrib_summary = contributions_df.copy()
        contrib_summary = contrib_summary.sort_values('contribution_pct', ascending=False)
        tables['contribution_summary'] = contrib_summary
        
        # Table 2: Optimization Recommendations (base scenario only)
        base_recommendations = optimization_df[optimization_df['scenario'] == 'base'].copy()
        base_recommendations['change_abs'] = (
            base_recommendations['optimized_spend'] - base_recommendations['current_spend']
        )
        base_recommendations = base_recommendations.sort_values('change_pct', ascending=False)
        tables['optimization_recommendations'] = base_recommendations
        
        # Table 3: Scenario Comparison
        scenario_summary = optimization_df.groupby('scenario').agg({
            'optimized_spend': 'sum',
            'current_spend': 'sum'
        }).reset_index()
        scenario_summary['budget_change'] = (
            scenario_summary['optimized_spend'] - scenario_summary['current_spend']
        )
        tables['scenario_comparison'] = scenario_summary
        
        return tables
    
    def _persist_outputs(
        self,
        summary_tables: Dict[str, pd.DataFrame],
        visualization_paths: Dict[str, str]
    ) -> Dict[str, str]:
        """Save insights, narratives, and summaries to disk."""
        decks_dir = Path("artifacts/decks")
        decks_dir.mkdir(parents=True, exist_ok=True)
        
        # Save insights JSON
        insights_path = decks_dir / "key_insights.json"
        with open(insights_path, 'w') as f:
            json.dump(self.insights, f, indent=2)
        
        # Save narratives
        narratives_path = decks_dir / "executive_narratives.txt"
        with open(narratives_path, 'w') as f:
            for section, text in self.narratives.items():
                f.write(f"=== {section.upper()} ===\n\n")
                f.write(text)
                f.write("\n\n")
        
        # Save summary tables to Excel
        excel_path = decks_dir / "mmx_summary_report.xlsx"
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            for table_name, table_df in summary_tables.items():
                sheet_name = table_name.replace('_', ' ').title()[:31]  # Excel limit
                table_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Create master summary document
        summary_path = decks_dir / "executive_summary.md"
        self._create_executive_summary(summary_path)
        
        self.logger.info(f"Saved all outputs to {decks_dir}")
        
        return {
            "insights_json": str(insights_path),
            "narratives": str(narratives_path),
            "excel_report": str(excel_path),
            "executive_summary": str(summary_path),
            "visualizations": visualization_paths
        }
    
    def _create_executive_summary(self, output_path: Path) -> None:
        """Create markdown executive summary."""
        with open(output_path, 'w') as f:
            f.write("# MMX Analysis - Executive Summary\n\n")
            
            # Overview
            f.write("## Overview\n\n")
            if 'overview' in self.narratives:
                f.write(self.narratives['overview'])
                f.write("\n\n")
            
            # Key Insights
            f.write("## Key Insights\n\n")
            for insight in self.insights:
                f.write(f"### {insight.get('title', 'Insight')}\n\n")
                f.write(f"**{insight.get('metric', '')}**\n\n")
                f.write(f"{insight.get('description', '')}\n\n")
            
            # Recommendations
            f.write("## Recommendations\n\n")
            if 'recommendations' in self.narratives:
                f.write(self.narratives['recommendations'])
                f.write("\n\n")
            
            # Next Steps
            f.write("## Next Steps\n\n")
            if 'next_steps' in self.narratives:
                f.write(self.narratives['next_steps'])
                f.write("\n\n")
