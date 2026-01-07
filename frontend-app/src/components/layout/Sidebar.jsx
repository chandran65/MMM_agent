import React from 'react';
import { NavLink } from 'react-router-dom';
import {
    LayoutDashboard,
    Database,
    LineChart,
    Settings,
    Layers,
    Zap,
    BookOpen
} from 'lucide-react';
import './Layout.css';

const Sidebar = () => {
    return (
        <aside className="sidebar">
            <div className="sidebar-header">
                <div className="logo-icon">
                    <Zap size={20} fill="currentColor" />
                </div>
                <span className="app-title">MMX Nexus</span>
            </div>

            <nav className="nav-links">
                <NavLink
                    to="/"
                    className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                >
                    <LayoutDashboard size={20} />
                    <span>Dashboard</span>
                </NavLink>

                <NavLink
                    to="/data"
                    className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                >
                    <Database size={20} />
                    <span>Data Studio</span>
                </NavLink>

                <NavLink
                    to="/analysis"
                    className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                >
                    <LineChart size={20} />
                    <span>Analysis & ROI</span>
                </NavLink>

                <NavLink
                    to="/insights"
                    className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                >
                    <BookOpen size={20} />
                    <span>Insights</span>
                </NavLink>

                <div style={{ marginTop: 'auto' }}>
                    <NavLink
                        to="/settings"
                        className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                    >
                        <Settings size={20} />
                        <span>Settings</span>
                    </NavLink>
                </div>
            </nav>
        </aside>
    );
};

export default Sidebar;
