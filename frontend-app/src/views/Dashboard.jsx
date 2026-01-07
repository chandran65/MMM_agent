import React from 'react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer
} from 'recharts';
import { TrendingUp, DollarSign, Target, Activity } from 'lucide-react';
import { motion } from 'framer-motion';

const StatCard = ({ title, value, change, icon: Icon, color }) => (
    <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel"
        style={{ padding: '1.5rem', borderRadius: 'var(--radius-lg)' }}
    >
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>{title}</span>
            <Icon size={20} color={color} />
        </div>
        <div style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem' }}>
            {value}
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', fontSize: '0.875rem' }}>
            <span style={{ color: 'var(--success)', fontWeight: 500 }}>{change}</span>
            <span style={{ color: 'var(--text-muted)' }}>vs last period</span>
        </div>
    </motion.div>
);

const Dashboard = () => {
    // Mock Data (Updated with real channels from finding)
    const data = [
        { name: 'Branded Search', roi: 1.5, spend: 2000 },
        { name: 'Nonbranded', roi: 1.2, spend: 400 },
        { name: 'Facebook', roi: 2.1, spend: 1000 },
        { name: 'Print', roi: 1.1, spend: 370 },
        { name: 'OOH', roi: 1.8, spend: 180 },
        { name: 'TV', roi: 3.5, spend: 270 },
        { name: 'Radio', roi: 2.3, spend: 520 },
    ];

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {/* Stats Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.5rem' }}>
                <StatCard
                    title="Model Quality (R²)"
                    value="-0.056"
                    change="Stable"
                    icon={Target}
                    color="#ef4444"
                />
                <StatCard
                    title="Top Driver"
                    value="Radio"
                    change="2.3% Contribution"
                    icon={TrendingUp}
                    color="#3b82f6"
                />
                <StatCard
                    title="Optimization Potential"
                    value="High"
                    change="2507% Realloc."
                    icon={DollarSign}
                    color="#10b981"
                />
                <StatCard
                    title="Active Channels"
                    value="7"
                    change="All Underinvested"
                    icon={Activity}
                    color="#f59e0b"
                />
            </div>

            {/* Charts Section */}
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem', height: '400px' }}>
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2 }}
                    className="glass-panel"
                    style={{ padding: '1.5rem', borderRadius: 'var(--radius-lg)', display: 'flex', flexDirection: 'column' }}
                >
                    <h3 style={{ marginBottom: '1.5rem', fontWeight: 600 }}>Channel ROI Performance</h3>
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={data}>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.3} />
                            <XAxis dataKey="name" stroke="var(--text-secondary)" />
                            <YAxis stroke="var(--text-secondary)" />
                            <Tooltip
                                contentStyle={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border)' }}
                                itemStyle={{ color: 'var(--text-primary)' }}
                            />
                            <Bar dataKey="roi" fill="var(--accent)" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 }}
                    className="glass-panel"
                    style={{ padding: '1.5rem', borderRadius: 'var(--radius-lg)' }}
                >
                    <h3 style={{ marginBottom: '1.5rem', fontWeight: 600 }}>Optimization Impact</h3>
                    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <div style={{ padding: '1rem', background: 'rgba(59, 130, 246, 0.1)', borderRadius: 'var(--radius-md)' }}>
                            <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Projected Revenue Uplift</div>
                            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent)' }}>+$450k</div>
                        </div>

                        <div style={{ padding: '1rem', background: 'rgba(16, 185, 129, 0.1)', borderRadius: 'var(--radius-md)' }}>
                            <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Efficiency Gain</div>
                            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--success)' }}>+18%</div>
                        </div>

                        <div style={{ marginTop: 'auto', padding: '1rem', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)' }}>
                            <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Top Recommendation</div>
                            <div>Increase <b>TV Spend</b> by 15% to capture available saturation headroom.</div>
                        </div>
                    </div>
                </motion.div>
            </div>
        </div>
    );
};

export default Dashboard;
