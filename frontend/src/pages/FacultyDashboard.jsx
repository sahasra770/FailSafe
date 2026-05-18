import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { facultyAPI } from '../api/axios';
import { Users, AlertTriangle, ShieldCheck, Activity, Eye, Zap } from 'lucide-react';

const FacultyDashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const fetchDashboard = async () => {
    try {
      const res = await facultyAPI.getDashboard();
      setData(res);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const handleBatchPredict = async () => {
    try {
      await facultyAPI.batchPredict();
      fetchDashboard();
    } catch (err) {
      alert("Failed to run batch prediction");
    }
  };

  if (loading) return <div className="container">Loading dashboard...</div>;

  return (
    <div className="container animate-fade-in">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1>Faculty Dashboard</h1>
          <p>Monitor your students' academic health and risk factors.</p>
        </div>
        <button className="btn" onClick={handleBatchPredict}>
          <Zap size={18} fill="currentColor" /> Run Batch Prediction
        </button>
      </div>

      <div className="dashboard-grid">
        <div className="card stat-card">
          <div className="flex justify-between items-center">
            <h3>Total Students</h3>
            <Users size={24} color="var(--primary)" />
          </div>
          <div className="stat-value">{data?.stats.total_students || 0}</div>
        </div>
        <div className="card stat-card">
          <div className="flex justify-between items-center">
            <h3>High Risk</h3>
            <AlertTriangle size={24} color="var(--risk-high)" />
          </div>
          <div className="stat-value stat-high">{data?.stats.high_risk || 0}</div>
        </div>
        <div className="card stat-card">
          <div className="flex justify-between items-center">
            <h3>Medium Risk</h3>
            <Activity size={24} color="var(--risk-medium)" />
          </div>
          <div className="stat-value stat-medium">{data?.stats.medium_risk || 0}</div>
        </div>
        <div className="card stat-card">
          <div className="flex justify-between items-center">
            <h3>Low Risk</h3>
            <ShieldCheck size={24} color="var(--risk-low)" />
          </div>
          <div className="stat-value stat-low">{data?.stats.low_risk || 0}</div>
        </div>
      </div>

      <div className="card">
        <h2 className="mb-4">Student Overview</h2>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Roll No</th>
                <th>Name</th>
                <th>Department</th>
                <th>Sem</th>
                <th>Risk Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {data?.students?.map(student => (
                <tr key={student.student_id}>
                  <td style={{ fontWeight: 500 }}>{student.roll_no}</td>
                  <td>{student.name}</td>
                  <td>{student.department}</td>
                  <td>{student.semester}</td>
                  <td>
                    <span className={`badge ${student.risk_label.toLowerCase()}`}>
                      <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'currentColor', marginRight: '6px', display: 'inline-block' }}></span>
                      {student.risk_label}
                    </span>
                  </td>
                  <td>
                    <button 
                      className="btn btn-secondary" 
                      style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}
                      onClick={() => navigate(`/student/${student.student_id}`)}
                    >
                      <Eye size={14} /> View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default FacultyDashboard;
