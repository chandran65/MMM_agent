"""
Narrative Generator

Generates executive narratives and stakeholder-ready text insights.
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import logging


class NarrativeGenerator:
    """Generate narrative insights from MMX outputs."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_narratives(
        self,
        insights: List[Dict],
        contributions_df: pd.DataFrame,
        optimization_df: pd.DataFrame,
        model_metrics: Dict
    ) -> Dict[str, str]:
        """
        Generate all narrative sections.
        
        Args:
            insights: List of insights
            contributions_df: Channel contributions
            optimization_df: Optimization results
            model_metrics: Model metrics
            
        Returns:
            Dictionary of narrative sections
        """
        narratives = {
            'overview': self._generate_overview(model_metrics, contributions_df),
            'model_performance': self._generate_model_performance_narrative(model_metrics),
            'channel_insights': self._generate_channel_insights(contributions_df),
            'optimization_insights': self._generate_optimization_insights(optimization_df),
            'recommendations': self._generate_recommendations(insights, optimization_df),
            'next_steps': self._generate_next_steps()
        }
        
        return narratives
    
    def _generate_overview(
        self,
        model_metrics: Dict,
        contributions_df: pd.DataFrame
    ) -> str:
        """Generate overview narrative."""
        r_squared = model_metrics.get('r_squared', 0)
        n_channels = len(contributions_df)
        
        text = f"""This Marketing Mix Modeling (MMM) analysis evaluates the effectiveness of {n_channels} marketing channels 
in driving incremental sales. The model achieves an R² of {r_squared:.3f}, indicating that it explains 
{r_squared*100:.1f}% of the variance in sales performance.

The analysis includes baseline estimation, channel contribution attribution, response curve modeling, 
and budget optimization to provide actionable recommendations for marketing spend allocation."""
        
        return text
    
    def _generate_model_performance_narrative(self, model_metrics: Dict) -> str:
        """Generate model performance narrative."""
        r2 = model_metrics.get('r_squared', 0)
        mape = model_metrics.get('mape', 0)
        
        quality_assessment = "excellent" if r2 > 0.8 else "good" if r2 > 0.7 else "acceptable"
        
        text = f"""Model Performance Summary:

The MMM model demonstrates {quality_assessment} predictive performance with an R² of {r2:.3f} and 
a Mean Absolute Percentage Error (MAPE) of {mape:.2f}%. This indicates the model is reliable for 
budget allocation decisions.

Key performance metrics:
- R-squared: {r2:.3f}
- MAPE: {mape:.2f}%
- Adjusted R²: {model_metrics.get('adjusted_r_squared', r2):.3f}

The model successfully captures the relationship between marketing spend and sales outcomes, 
accounting for saturation effects and carryover (adstock) from previous periods."""
        
        return text
    
    def _generate_channel_insights(self, contributions_df: pd.DataFrame) -> str:
        """Generate channel-specific insights."""
        if contributions_df.empty:
            return "No channel contribution data available."
        
        # Sort by contribution
        sorted_df = contributions_df.sort_values('contribution_pct', ascending=False)
        
        text = "Channel Contribution Analysis:\n\n"
        
        for idx, row in sorted_df.iterrows():
            channel = row['channel']
            contrib_pct = row['contribution_pct']
            contrib_value = row.get('contribution', 0)
            
            text += f"- **{channel}**: Contributes {contrib_pct:.1f}% of incremental sales "
            text += f"(${contrib_value:,.0f})\n"
        
        # Identify top 3
        top_3 = sorted_df.head(3)['channel'].tolist()
        text += f"\n**Top 3 channels** ({', '.join(top_3)}) drive "
        text += f"{sorted_df.head(3)['contribution_pct'].sum():.1f}% of total marketing impact.\n"
        
        return text
    
    def _generate_optimization_insights(self, optimization_df: pd.DataFrame) -> str:
        """Generate optimization insights."""
        base_scenario = optimization_df[optimization_df['scenario'] == 'base']
        
        if base_scenario.empty:
            return "No optimization results available."
        
        # Channels with significant changes
        increase_channels = base_scenario[base_scenario['change_pct'] > 0.10]
        decrease_channels = base_scenario[base_scenario['change_pct'] < -0.10]
        
        text = "Optimization Recommendations:\n\n"
        
        if not increase_channels.empty:
            text += "**Channels to Increase:**\n"
            for _, row in increase_channels.iterrows():
                text += f"- {row['channel']}: +{row['change_pct']*100:.1f}% "
                text += f"(${row['change_abs']:,.0f})\n" if 'change_abs' in row else "\n"
            text += "\n"
        
        if not decrease_channels.empty:
            text += "**Channels to Decrease:**\n"
            for _, row in decrease_channels.iterrows():
                text += f"- {row['channel']}: {row['change_pct']*100:.1f}% "
                text += f"(${row['change_abs']:,.0f})\n" if 'change_abs' in row else "\n"
            text += "\n"
        
        text += "These reallocations are based on maximizing incremental sales while respecting "
        text += "channel-specific constraints and saturation effects."
        
        return text
    
    def _generate_recommendations(
        self,
        insights: List[Dict],
        optimization_df: pd.DataFrame
    ) -> str:
        """Generate actionable recommendations."""
        text = "Strategic Recommendations:\n\n"
        
        text += "1. **Implement Budget Reallocation**: Follow the optimized allocation to maximize ROI. "
        text += "The recommended changes are designed to improve efficiency while maintaining brand presence.\n\n"
        
        text += "2. **Monitor Channel Saturation**: Channels operating beyond optimal efficiency should "
        text += "be scaled back to avoid diminishing returns.\n\n"
        
        text += "3. **Invest in High-Performing Channels**: Increase allocation to channels showing strong "
        text += "contribution and room for growth.\n\n"
        
        text += "4. **Test and Learn**: Implement changes incrementally and monitor performance to validate "
        text += "model predictions.\n\n"
        
        text += "5. **Regular Model Updates**: Refresh the MMM model quarterly to incorporate new data and "
        text += "market dynamics.\n"
        
        return text
    
    def _generate_next_steps(self) -> str:
        """Generate next steps."""
        text = """Next Steps:

1. **Stakeholder Review**: Present findings to marketing leadership and finance teams
2. **Budget Planning**: Incorporate recommendations into next period's budget allocation
3. **Implementation**: Execute budget reallocation across channels
4. **Monitoring**: Set up tracking dashboards to monitor performance vs. predictions
5. **Model Refresh**: Schedule quarterly model updates to maintain accuracy

**Timeline**: Recommended implementation over 2-3 months with phased rollout to minimize risk."""
        
        return text
