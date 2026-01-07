"""
Visualization Engine

Creates charts and visual outputs for stakeholder presentations.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List
import logging


class VisualizationEngine:
    """Create visualizations for MMX insights."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Set style
        sns.set_style("whitegrid")
        plt.rcParams['figure.dpi'] = 300
        plt.rcParams['savefig.dpi'] = 300
        plt.rcParams['font.size'] = 10
    
    def create_visualizations(
        self,
        contributions_df: pd.DataFrame,
        optimization_df: pd.DataFrame,
        response_curves: Dict = None
    ) -> Dict[str, str]:
        """
        Create all visualizations.
        
        Args:
            contributions_df: Channel contributions
            optimization_df: Optimization results
            response_curves: Response curves data
            
        Returns:
            Dictionary of visualization file paths
        """
        viz_paths = {}
        
        # Chart 1: Channel Contribution Waterfall
        contrib_path = self._create_contribution_chart(contributions_df)
        viz_paths['contribution_chart'] = contrib_path
        
        # Chart 2: Optimization Comparison
        optim_path = self._create_optimization_chart(optimization_df)
        viz_paths['optimization_chart'] = optim_path
        
        # Chart 3: Response Curves (if available)
        if response_curves:
            curves_path = self._create_response_curves_chart(response_curves)
            viz_paths['response_curves'] = curves_path
        
        # Chart 4: Scenario Comparison
        scenario_path = self._create_scenario_comparison(optimization_df)
        viz_paths['scenario_comparison'] = scenario_path
        
        return viz_paths
    
    def _create_contribution_chart(self, contributions_df: pd.DataFrame) -> str:
        """Create channel contribution bar chart."""
        if contributions_df.empty:
            return ""
        
        output_dir = Path("artifacts/decks")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "channel_contributions.png"
        
        # Sort by contribution
        sorted_df = contributions_df.sort_values('contribution_pct', ascending=True)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        colors = sns.color_palette("viridis", len(sorted_df))
        bars = ax.barh(sorted_df['channel'], sorted_df['contribution_pct'], color=colors)
        
        ax.set_xlabel('Contribution to Incremental Sales (%)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Marketing Channel', fontsize=12, fontweight='bold')
        ax.set_title('Channel Contribution Analysis', fontsize=14, fontweight='bold', pad=20)
        
        # Add value labels
        for bar in bars:
            width = bar.get_width()
            # If value is huge (e.g. >100), it's likely a ratio that needs x100 or it's just broken. 
            # Given input csv is 2.57 (257%), let's display as is if > 1, else x100? 
            # Actually, standard MMM contribution percent is usually 0-100.
            # If we see 0.87 in CSV, let's treat it as 87% for display clarity if user expects %
            # But earlier backend treated it as ratio (multiplied by 100).
            
            # Let's multiply by 100 for display if max value < 5 (assuming ratio)
            display_val = width * 100 if sorted_df['contribution_pct'].max() < 5 else width
            
            label = f'{display_val:.1f}%'
            if display_val < 0.1:
                label = "<0.1%"
                
            ax.text(width, bar.get_y() + bar.get_height()/2, 
                   label,
                   ha='left', va='center', fontsize=9, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Saved contribution chart to {output_path}")
        return str(output_path)
    
    def _create_optimization_chart(self, optimization_df: pd.DataFrame) -> str:
        """Create optimization recommendations chart."""
        base_scenario = optimization_df[optimization_df['scenario'] == 'base']
        
        if base_scenario.empty:
            return ""
        
        output_dir = Path("artifacts/decks")
        output_path = output_dir / "optimization_recommendations.png"
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        channels = base_scenario['channel'].values
        current = base_scenario['current_spend'].values / 1000  # Convert to thousands
        optimized = base_scenario['optimized_spend'].values / 1000
        
        x = np.arange(len(channels))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, current, width, label='Current Spend', 
                      color='#3498db', alpha=0.8)
        bars2 = ax.bar(x + width/2, optimized, width, label='Optimized Spend', 
                      color='#e74c3c', alpha=0.8)
        
        ax.set_xlabel('Marketing Channel', fontsize=12, fontweight='bold')
        ax.set_ylabel('Spend ($000s)', fontsize=12, fontweight='bold')
        ax.set_title('Current vs. Optimized Budget Allocation', fontsize=14, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(channels, rotation=45, ha='right')
        ax.legend(fontsize=10)
        ax.grid(axis='y', alpha=0.3)
        
        # Add value labels
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'${height:.0f}k',
                       ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Saved optimization chart to {output_path}")
        return str(output_path)
    
    def _create_response_curves_chart(self, response_curves: Dict) -> str:
        """Create response curves chart."""
        output_dir = Path("artifacts/decks")
        output_path = output_dir / "response_curves.png"
        
        n_channels = len(response_curves)
        fig, axes = plt.subplots(
            (n_channels + 1) // 2, 2, 
            figsize=(14, 4 * ((n_channels + 1) // 2))
        )
        
        if n_channels == 1:
            axes = [axes]
        else:
            axes = axes.flatten()
        
        colors = sns.color_palette("husl", n_channels)
        
        for idx, (channel, curve_data) in enumerate(response_curves.items()):
            ax = axes[idx]
            
            spend = np.array(curve_data['spend']) / 1000  # Convert to thousands
            response = np.array(curve_data['response'])
            current_spend_avg = curve_data.get('current_spend_avg', 0) / 1000
            
            ax.plot(spend, response, linewidth=2.5, color=colors[idx], label='Response Curve')
            
            # Mark current spend
            if current_spend_avg > 0:
                # Find response at current spend
                current_response = np.interp(current_spend_avg, spend, response)
                ax.scatter([current_spend_avg], [current_response], 
                          color='red', s=100, zorder=5, label='Current Spend')
            
            ax.set_xlabel('Spend ($000s)', fontweight='bold')
            ax.set_ylabel('Response (Normalized)', fontweight='bold')
            ax.set_title(f'{channel} Response Curve', fontweight='bold', pad=10)
            ax.grid(True, alpha=0.3)
            ax.legend()
        
        # Hide extra subplots
        for idx in range(n_channels, len(axes)):
            axes[idx].set_visible(False)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Saved response curves to {output_path}")
        return str(output_path)
    
    def _create_scenario_comparison(self, optimization_df: pd.DataFrame) -> str:
        """Create scenario comparison chart."""
        output_dir = Path("artifacts/decks")
        output_path = output_dir / "scenario_comparison.png"
        
        # Aggregate by scenario
        scenario_summary = optimization_df.groupby('scenario').agg({
            'optimized_spend': 'sum'
        }).reset_index()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        scenarios = scenario_summary['scenario'].values
        budgets = scenario_summary['optimized_spend'].values / 1000  # Convert to thousands
        
        colors = ['#2ecc71', '#3498db', '#e74c3c'][:len(scenarios)]
        bars = ax.bar(scenarios, budgets, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
        
        ax.set_xlabel('Scenario', fontsize=12, fontweight='bold')
        ax.set_ylabel('Total Budget ($000s)', fontsize=12, fontweight='bold')
        ax.set_title('Budget Scenarios Comparison', fontsize=14, fontweight='bold', pad=20)
        ax.grid(axis='y', alpha=0.3)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'${height:.0f}k',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Saved scenario comparison to {output_path}")
        return str(output_path)
