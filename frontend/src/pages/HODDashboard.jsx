import React, { useEffect, useState } from 'react';
import { hodAPI } from '../api/axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { AlertTriangle, ShieldCheck, Activity } from 'lucide-react';

const HODDashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await hodAPI.getDashboard();
        setData(res);
        setLoading(false);
      } catch (err) {
        console.error(err);
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div className="container">Loading dashboard...</div>;

  return (
    <div className="container animate-fade-in">
      <h1 className="mb-2">Department Overview</h1>
      <p className="mb-8">Head of Department analytics and department-wide risk monitoring.</p>

      <div className="dashboard-grid">
        <div className="card stat-card">
          <div className="flex justify-between items-center">
            <h3>Critical Cases (High Risk)</h3>
            <AlertTriangle size={24} color="var(--risk-high)" />
          </div>
          <div className="stat-value stat-high">{data?.stats.critical_cases || 0}</div>
        </div>
        <div className="card stat-card">
          <div className="flex justify-between items-center">
            <h3>Active Interventions</h3>
            <Activity size={24} color="var(--primary)" />
          </div>
          <div className="stat-value">{data?.stats.total_interventions - (data?.stats.completed_interventions || 0)}</div>
        </div>
        <div className="card stat-card">
          <div className="flex justify-between items-center">
            <h3>Completed Interventions</h3>
            <ShieldCheck size={24} color="var(--risk-low)" />
          </div>
          <div className="stat-value stat-low">{data?.stats.completed_interventions || 0}</div>
        </div>
      </div>

      <div className="card" style={{ height: '500px' }}>
        <h2 className="mb-6">Risk Trends Over Time</h2>
        <div style={{ width: '100%', height: 'calc(100% - 40px)' }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={data?.trends}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis 
                dataKey="date" 
                stroke="var(--text-muted)" 
                tick={{ fill: 'var(--text-muted)' }}
                tickLine={false}
                axisLine={false}
                dy={10}
              />
              <YAxis 
                stroke="var(--text-muted)" 
                tick={{ fill: 'var(--text-muted)' }}
                tickLine={false}
                axisLine={false}
                dx={-10}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'var(--glass-bg)', 
                  border: '1px solid var(--border)',
                  backdropFilter: 'blur(12px)',
                  borderRadius: '0.75rem',
                  color: 'white'
                }}
                itemStyle={{ fontWeight: 500 }}
              />
              <Legend wrapperStyle={{ paddingTop: '20px' }} />
              <Line type="monotone" dataKey="High" stroke="var(--risk-high)" strokeWidth={4} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 8, strokeWidth: 0 }} />
              <Line type="monotone" dataKey="Medium" stroke="var(--risk-medium)" strokeWidth={4} dot={{ r: 4, strokeWidth: 2 }} />
              <Line type="monotone" dataKey="Low" stroke="var(--risk-low)" strokeWidth={4} dot={{ r: 4, strokeWidth: 2 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default HODDashboard;
