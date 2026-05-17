import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { studentAPI, interventionAPI } from '../api/axios';
import { ArrowLeft, Plus, CheckCircle, Info, BarChart2 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const StudentDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newIntervention, setNewIntervention] = useState('');

  const fetchData = async () => {
    try {
      // Fetch both dashboard (for interventions and basic info) and history (for SHAP and predictions)
      const [dashRes, histRes] = await Promise.all([
        studentAPI.getDashboard(id),
        studentAPI.getHistory(id)
      ]);
      setData(dashRes);
      setHistory(histRes);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [id]);

  const handleAddIntervention = async (e) => {
    e.preventDefault();
    if (!newIntervention) return;
    try {
      await interventionAPI.create({
        student_id: id,
        type: "Manual Assignment",
        description: newIntervention
      });
      setNewIntervention('');
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleUpdateStatus = async (interventionId, newStatus) => {
    try {
      await interventionAPI.updateStatus(interventionId, newStatus);
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) return <div className="container">Loading details...</div>;
  
  const latestPrediction = history?.length > 0 ? history[0] : null;
  const riskLabel = latestPrediction?.risk_label?.toLowerCase() || 'low';
  const riskScore = Math.round(latestPrediction?.risk_score || 0);

  // Prepare SHAP data for chart
  let shapData = [];
  if (latestPrediction?.shap_values) {
    // Convert dictionary to array
    const entries = Object.entries(latestPrediction.shap_values);
    // Sort by absolute impact (highest first) and take top 5
    shapData = entries
      .map(([key, val]) => ({
        feature: key.charAt(0).toUpperCase() + key.slice(1), 
        impact: Number(val.toFixed(4)),
        absImpact: Math.abs(val)
      }))
      .sort((a, b) => b.absImpact - a.absImpact)
      .slice(0, 5);
  }

  // Custom tooltip for SHAP BarChart
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const isPositive = payload[0].value > 0;
      return (
        <div style={{ backgroundColor: 'var(--glass-bg)', padding: '10px', border: '1px solid var(--border)', borderRadius: '8px' }}>
          <p style={{ margin: 0, fontWeight: 'bold', color: 'white' }}>{payload[0].payload.feature}</p>
          <p style={{ margin: 0, color: isPositive ? 'var(--risk-high)' : 'var(--risk-low)' }}>
            Impact: {payload[0].value > 0 ? '+' : ''}{payload[0].value}
          </p>
          <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-muted)' }}>
            {isPositive ? 'Increases failure risk' : 'Decreases failure risk'}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="container animate-fade-in">
      <button 
        className="btn btn-secondary mb-4" 
        onClick={() => navigate(-1)}
        style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}
      >
        <ArrowLeft size={16} /> Back
      </button>
      
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1>{data?.student.roll_no}</h1>
          <p>Detailed academic profile and AI risk analysis.</p>
        </div>
      </div>

      <div className="dashboard-grid">
        {/* Risk Profile Gauge */}
        <div className="card flex flex-col items-center">
          <h2 className="w-full text-center">Current Risk Profile</h2>
          
          {latestPrediction ? (
            <>
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
              
              <div className="text-center mt-4 mb-6">
                <span className={`badge ${riskLabel}`} style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'currentColor', marginRight: '8px', display: 'inline-block' }}></span>
                  {latestPrediction.risk_label} Risk Level
                </span>
                <div className="mt-2" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Last predicted: {new Date(latestPrediction.predicted_on).toLocaleString()}
                </div>
              </div>
            </>
          ) : (
             <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
               No predictions available for this student.
             </div>
          )}
        </div>

        {/* Risk Factors & SHAP Values */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <BarChart2 size={24} color="var(--primary)" />
            <h2 style={{ margin: 0 }}>Top Risk Factors</h2>
          </div>
          
          <div className="explanation-box w-full mb-6">
            <div className="flex items-center gap-2 mb-2">
              <Info size={16} color="var(--primary)" />
              <h3 style={{ margin: 0, fontSize: '0.875rem', color: 'var(--text-main)' }}>AI Explanation</h3>
            </div>
            <p style={{ margin: 0, fontSize: '0.875rem' }}>{data?.explanation || "No explanation available."}</p>
          </div>

          {shapData.length > 0 ? (
            <div style={{ width: '100%', height: '250px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={shapData}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--border)" />
                  <XAxis type="number" stroke="var(--text-muted)" tick={{ fontSize: 12 }} />
                  <YAxis dataKey="feature" type="category" stroke="var(--text-muted)" tick={{ fontSize: 12 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="impact" radius={[0, 4, 4, 0]}>
                    {shapData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.impact > 0 ? 'var(--risk-high)' : 'var(--risk-low)'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <div className="text-center mt-2" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Feature Impact (SHAP Values)
              </div>
            </div>
          ) : (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              No SHAP data available.
            </div>
          )}
        </div>
      </div>

      {/* Interventions */}
      <div className="card mt-4">
        <h2 className="mb-4">Intervention Plan</h2>
        
        <form onSubmit={handleAddIntervention} className="flex gap-4 mb-8" style={{ alignItems: 'flex-end' }}>
          <div className="w-full">
            <label className="form-label">Assign New Intervention</label>
            <input 
              type="text" 
              className="form-input" 
              placeholder="e.g., Mandatory tutoring on Fridays"
              value={newIntervention}
              onChange={(e) => setNewIntervention(e.target.value)}
            />
          </div>
          <button type="submit" className="btn" style={{ whiteSpace: 'nowrap' }}>
            <Plus size={18} /> Assign
          </button>
        </form>

        {data?.interventions?.length > 0 ? (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Description</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {data.interventions.map(inv => (
                  <tr key={inv.id}>
                    <td>{inv.type}</td>
                    <td>{inv.description}</td>
                    <td>
                      <span className={`badge ${inv.status === 'complete' ? 'low' : 'medium'}`}>
                        {inv.status}
                      </span>
                    </td>
                    <td>
                      {inv.status !== 'complete' && (
                        <button 
                          className="btn btn-secondary" 
                          style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem', color: 'var(--risk-low)', borderColor: 'var(--risk-low-border)' }}
                          onClick={() => handleUpdateStatus(inv.id, 'complete')}
                        >
                          <CheckCircle size={14} /> Mark Complete
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: '2rem', textAlign: 'center', background: 'rgba(0,0,0,0.2)', borderRadius: '0.75rem', border: '1px dashed var(--border)', color: 'var(--text-muted)' }}>
            No interventions assigned yet.
          </div>
        )}
      </div>
    </div>
  );
};

export default StudentDetail;