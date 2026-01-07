import React from 'react';
import { motion } from 'framer-motion';

const Analysis = () => {
    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {/* Header */}
            <div>
                <h2 style={{ marginBottom: '0.5rem' }}>Response Curve Analysis</h2>
                <p style={{ color: 'var(--text-secondary)' }}>
                    Analyze saturation points and diminishing returns for each media channel.
                </p>
            </div>

            {/* Response Curves Visualization */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-panel"
                style={{ padding: '2rem', borderRadius: 'var(--radius-lg)' }}
            >
                <h3 style={{ marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '1rem' }}>
                    Saturation Curves
                </h3>
                <div style={{
                    width: '100%',
                    borderRadius: 'var(--radius-md)',
                    overflow: 'hidden',
                    border: '1px solid var(--border)'
                }}>
                    <img
                        src="/assets/response_curves.png"
                        alt="Response Curves"
                        style={{ width: '100%', height: 'auto', display: 'block' }}
                    />
                </div>
                <div style={{ marginTop: '1.5rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                    <div style={{ padding: '1rem', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}>
                        <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Metric</div>
                        <div style={{ fontWeight: 600 }}>Incremental Sales</div>
                    </div>
                    <div style={{ padding: '1rem', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}>
                        <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Diminishing Point</div>
                        <div style={{ fontWeight: 600 }}>Identified for 4 Channels</div>
                    </div>
                </div>
            </motion.div>

            {/* Trend Analysis */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="glass-panel"
                style={{ padding: '2rem', borderRadius: 'var(--radius-lg)' }}
            >
                <h3 style={{ marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '1rem' }}>
                    Trend Decomposition
                </h3>
                <div style={{
                    width: '100%',
                    borderRadius: 'var(--radius-md)',
                    overflow: 'hidden',
                    border: '1px solid var(--border)'
                }}>
                    <img
                        src="/assets/trends_visualization.png"
                        alt="Trend Analysis"
                        style={{ width: '100%', height: 'auto', display: 'block' }}
                    />
                </div>
            </motion.div>
        </div>
    );
};

export default Analysis;
