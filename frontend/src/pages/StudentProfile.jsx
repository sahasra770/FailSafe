import React, { useEffect, useState } from 'react';
import { studentAPI } from '../api/axios';
import { Info, Lightbulb, CheckCircle2, AlertCircle } from 'lucide-react';

const StudentProfile = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await studentAPI.getDashboard(1); 
        setData(res);
        setLoading(false);
      } catch (err) {
        console.error(err);
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div className="container">Loading your profile...</div>;

  const riskLabel = data?.latest_prediction?.risk_label?.toLowerCase() || 'low';
  const riskScore = Math.round(data?.latest_prediction?.risk_score || 0);

  return (
    <div className="container animate-fade-in">
      <h1 className="mb-2">My Academic Profile</h1>
      <p className="mb-8">Track your progress and view personalized recommendations.</p>

      <div className="dashboard-grid">
        <div className="card flex flex-col items-center">
          <h2 className="w-full text-center">Current Academic Standing</h2>
          
          <div className="gauge-wrapper">
            <div className="gauge-circle" style={{ 
              background: `conic-gradient(var(--risk-${riskLabel}) ${riskScore}%, rgba(255,255,255,0.05) 0)` 
            }}>
              <div className="gauge-inner">
                <span className="gauge-score" style={{ color: `var(--risk-${riskLabel})` }}>
                  {riskScore}%
                </span>
                <span className="gauge-label">Risk Score</span>
              </div>
            </div>
          </div>
          
          <div className="text-center mt-4">
            <span className={`badge ${riskLabel}`} style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'currentColor', marginRight: '8px', display: 'inline-block' }}></span>
              {data?.latest_prediction?.risk_label || 'Unknown'} Risk
            </span>
          </div>
        </div>

        <div className="card">
          <h2 className="flex items-center gap-2 mb-6">
            <Info size={24} color="var(--primary)" /> 
            Areas for Improvement
          </h2>
          
          <div className="explanation-box mb-6">
            <p style={{ margin: 0 }}>{data?.explanation}</p>
          </div>
          
          <h3 className="flex items-center gap-2 mt-4 mb-4" style={{ color: 'var(--text-main)' }}>
            <Lightbulb size={18} color="var(--risk-medium)" /> 
            Improvement Tips
          </h3>
          
          <ul style={{ listStyleType: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <li className="flex items-start gap-3">
              <CheckCircle2 size={18} color="var(--risk-low)" style={{ flexShrink: 0, marginTop: '2px' }} />
              <span style={{ color: 'var(--text-muted)' }}>Attend all upcoming lectures to improve your attendance score.</span>
            </li>
            <li className="flex items-start gap-3">
              <CheckCircle2 size={18} color="var(--risk-low)" style={{ flexShrink: 0, marginTop: '2px' }} />
              <span style={{ color: 'var(--text-muted)' }}>Submit all assignments on time and double-check requirements.</span>
            </li>
            <li className="flex items-start gap-3">
              <CheckCircle2 size={18} color="var(--risk-low)" style={{ flexShrink: 0, marginTop: '2px' }} />
              <span style={{ color: 'var(--text-muted)' }}>Reach out to your faculty advisor during office hours for guidance.</span>
            </li>
          </ul>
        </div>
      </div>

      <div className="card mt-4">
        <h2 className="mb-4">My Intervention Plan</h2>
        {data?.interventions?.length > 0 ? (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Task/Intervention</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {data.interventions.map(inv => (
                  <tr key={inv.id}>
                    <td>{inv.description}</td>
                    <td>
                      <span className={`badge ${inv.status === 'complete' ? 'low' : 'medium'}`}>
                        {inv.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-8 text-center" style={{ background: 'rgba(0,0,0,0.2)', borderRadius: '0.75rem', border: '1px dashed var(--border)' }}>
            <AlertCircle size={32} color="var(--text-muted)" style={{ marginBottom: '1rem' }} />
            <p style={{ margin: 0 }}>No interventions assigned. Keep up the good work!</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default StudentProfile;
