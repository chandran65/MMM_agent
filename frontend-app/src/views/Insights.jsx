import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Lightbulb, BookOpen, ArrowRight, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';

const InsightCard = ({ title, metric, description, category, delay }) => {
    let icon = Lightbulb;
    let color = 'var(--accent)';

    if (category === 'underinvestment') { icon = TrendingUp; color = 'var(--success)'; }
    if (category === 'overinvestment') { icon = AlertTriangle; color = 'var(--warning)'; }
    if (category === 'model_performance') { icon = CheckCircle; color = 'var(--text-secondary)'; }

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay }}
            className="glass-panel"
            style={{ padding: '1.5rem', borderRadius: 'var(--radius-lg)', display: 'flex', flexDirection: 'column', gap: '1rem' }}
        >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{ padding: '0.5rem', borderRadius: '8px', background: `rgba(59, 130, 246, 0.1)`, color: color }}>
                    <React.Fragment>
                        {React.createElement(icon, { size: 20 })}
                    </React.Fragment>
                </div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>{title}</h3>
            </div>

            {metric && (
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {metric}
                </div>
            )}

            <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                {description}
            </p>
        </motion.div>
    );
};

const Insights = () => {
    // In a real app, fetch from /api/pipeline/:id/results
    // For demo, we use the known insights structure
    const insightsData = [
        {
            category: "model_performance",
            title: "Model Quality",
            metric: "R² = -0.056",
            description: "The model is currently showing low explanatory power, likely due to strong seasonality in the input data derived from a limited 2-year window. We recommend adding more historical data."
        },
        {
            category: "top_performer",
            title: "Highest Contributing Channel",
            metric: "Radio (2.6%)",
            description: "Radio is currently driving the highest incremental sales among all media channels, despite relatively low spend."
        },
        {
            category: "optimization",
            title: "Optimization Potential",
            metric: "High Impact",
            description: "There is significant opportunity to improve ROI by reallocating budget from saturated channels to those with higher marginal returns."
        },
        {
            category: "underinvestment",
            title: "Growth Opportunities",
            metric: "7 Channels",
            description: "Our analysis suggests increasing spend in Branded Search, Nonbranded Search, Facebook, Print, OOH, TV, and Radio to capture availble market share."
        }
    ];

    return (
        <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '2rem' }}>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
                <div>
                    <h2 style={{ fontSize: '1.75rem', marginBottom: '0.5rem' }}>Strategic Insights</h2>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem' }}>
                        AI-generated analysis of your marketing mix performance.
                    </p>
                </div>
                <button style={{
                    display: 'flex', alignItems: 'center', gap: '0.5rem',
                    background: 'var(--bg-card)', border: '1px solid var(--border)',
                    color: 'var(--text-primary)', padding: '0.75rem 1.25rem', borderRadius: 'var(--radius-md)',
                    cursor: 'pointer'
                }}>
                    <BookOpen size={18} />
                    Download Full Report
                </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '1.5rem' }}>
                {insightsData.map((insight, idx) => (
                    <InsightCard
                        key={idx}
                        {...insight}
                        delay={idx * 0.1}
                    />
                ))}
            </div>

            {/* Narrative Section */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="glass-panel"
                style={{ padding: '2.5rem', borderRadius: 'var(--radius-xl)' }}
            >
                <h3 style={{ fontSize: '1.5rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '1rem' }}>
                    Executive Summary
                </h3>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', color: 'var(--text-secondary)', lineHeight: 1.8, fontSize: '1.05rem' }}>
                    <p>
                        <strong style={{ color: 'var(--text-primary)' }}>Overview:</strong> The current marketing mix is performing at a baseline level, but exhibits signs of non-optimal allocation. While <strong>Radio</strong> and <strong>TV</strong> are showing promise, the overall model fit suggests that external factors (seasonality) are playing a larger role than media spend alone.
                    </p>
                    <p>
                        <strong style={{ color: 'var(--text-primary)' }}>Recommendation:</strong> The algorithms have identified a substantial opportunity to increase efficiency. By shifting budget into the identifies growth channels, we project a potential uplift in revenue. Specifically, <strong>TV</strong> spend should be increased to test the saturation upper bounds.
                    </p>
                    <p>
                        <strong style={{ color: 'var(--text-primary)' }}>Next Steps:</strong> We recommend executing the "Base" optimization scenario for the upcoming quarter. Concurrent with this, additional granular data (daily level) should be collected to improve model precision.
                    </p>
                </div>
            </motion.div>
        </div>
    );
};

export default Insights;
