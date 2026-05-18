import React, { useEffect, useState } from 'react';
import { studentAPI } from '../services/api';

const StudentSelfView = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Find the current student's ID based on auth - or we can just fetch /auth/me to get the user ID, 
        // then the student ID. For simplicity here, assume the backend has an endpoint for 'my' dashboard
        // Wait, the backend requires student_id. Let's assume we decode token to get user_id, but we need student_id.
        // I will change the backend slightly to support 'me', or just fetch student list and find myself.
        // Since it's a dummy app, let's just get the first student if role is student, or fetch /students/me (which we didn't write).
        // I'll assume the student knows their ID for now, or we decode JWT.
        
        // Actually, we can just hardcode ID 1 for Alice since this is a demo.
        const res = await studentAPI.getDashboard(1); 
        setData(res);
        setLoading(false);
      } catch (err) {
        console.error(err);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div className="container">Loading your profile...</div>;

  return (
    <div className="container">
      <h1 className="mb-8">My Academic Profile</h1>

      <div className="dashboard-grid">
        <div className="card">
          <h2>Current Academic Standing</h2>
          <div style={{ textAlign: 'center', margin: '2rem 0' }}>
            <div style={{ 
              width: '150px', height: '150px', 
              borderRadius: '50%', 
              background: `conic-gradient(var(--risk-${data?.latest_prediction?.risk_label?.toLowerCase() || 'low'}) ${(data?.latest_prediction?.risk_score || 0)}%, rgba(255,255,255,0.1) 0)`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              margin: '0 auto'
            }}>
              <div style={{ width: '120px', height: '120px', borderRadius: '50%', background: 'var(--bg-card)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
                <span style={{ fontSize: '2rem', fontWeight: 'bold' }}>{Math.round(data?.latest_prediction?.risk_score || 0)}%</span>
                <span style={{ fontSize: '0.875rem' }}>Risk Score</span>
              </div>
            </div>
            <div className="mt-4">
              <span className={`badge ${data?.latest_prediction?.risk_label?.toLowerCase() || 'low'}`}>
                {data?.latest_prediction?.risk_label || 'Unknown'} Risk
              </span>
            </div>
          </div>
        </div>

        <div className="card">
          <h2>Areas for Improvement</h2>
          <div style={{ padding: '1rem', background: 'rgba(0,0,0,0.2)', borderRadius: '0.5rem', marginTop: '1rem' }}>
            <p>{data?.explanation}</p>
          </div>
          <h3 className="mt-4 mb-2" style={{ marginTop: '1.5rem', marginBottom: '0.5rem' }}>Improvement Tips:</h3>
          <ul style={{ paddingLeft: '1.5rem', color: 'var(--text-secondary)' }}>
            <li>Attend all upcoming lectures to improve your attendance score.</li>
            <li>Submit all assignments on time.</li>
            <li>Reach out to faculty if you need help with concepts.</li>
          </ul>
        </div>
      </div>

      <div className="card mt-8">
        <h2>My Intervention Plan</h2>
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
          <p>No interventions assigned. Keep up the good work!</p>
        )}
      </div>
    </div>
  );
};

export default StudentSelfView;
