import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import './Layout.css';
import { Bell, User } from 'lucide-react';

const Layout = () => {
    const location = useLocation();

    // Map route to page title
    const getPageTitle = (pathname) => {
        switch (pathname) {
            case '/': return 'Executive Dashboard';
            case '/data': return 'Data Studio';
            case '/analysis': return 'ROI Analysis';
            case '/insights': return 'Strategic Insights';
            case '/settings': return 'System Settings';
            default: return 'MMX Nexus';
        }
    };

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="main-content">
                <header className="top-bar">
                    <h1 style={{ fontSize: '1.25rem', fontWeight: 600 }}>
                        {getPageTitle(location.pathname)}
                    </h1>

                    <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                        <button style={{
                            background: 'none',
                            border: 'none',
                            color: 'var(--text-secondary)',
                            cursor: 'pointer'
                        }}>
                            <Bell size={20} />
                        </button>
                        <div style={{
                            width: 32,
                            height: 32,
                            borderRadius: '50%',
                            background: 'var(--bg-hover)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            border: '1px solid var(--border)'
                        }}>
                            <User size={18} />
                        </div>
                    </div>
                </header>

                <div className="page-content">
                    <Outlet />
                </div>
            </main>
        </div>
    );
};

export default Layout;
