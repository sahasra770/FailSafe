import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI } from '../api/axios';
import { Activity, ArrowRight, Lock, Mail } from 'lucide-react';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('password'); 
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const data = await authAPI.login(email, password);
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('role', data.role);
      
      if (data.role === 'faculty') navigate('/faculty');
      else if (data.role === 'hod') navigate('/hod');
      else if (data.role === 'student') navigate('/my-profile');
    } catch (err) {
      setError('Invalid credentials');
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="card animate-fade-in" style={{ width: '400px', maxWidth: '100%' }}>
        <div className="flex flex-col items-center mb-8">
          <div style={{ background: 'var(--primary-light)', padding: '1rem', borderRadius: '50%', marginBottom: '1rem' }}>
            <Activity color="var(--primary)" size={32} />
          </div>
          <h1 className="text-center" style={{ marginBottom: '0.25rem' }}>FAILSAFE</h1>
          <p className="text-center" style={{ fontSize: '0.875rem' }}>Student Failure Prediction System</p>
        </div>
        
        {error && <div className="text-error mb-4 text-center" style={{ background: 'var(--risk-high-bg)', padding: '0.75rem', borderRadius: '0.5rem', fontSize: '0.875rem' }}>{error}</div>}
        
        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label className="form-label">Email Address</label>
            <div style={{ position: 'relative' }}>
              <div style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}>
                <Mail size={18} />
              </div>
              <input 
                type="email" 
                className="form-input" 
                style={{ paddingLeft: '2.5rem' }}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="faculty@failsafe.com"
                required 
              />
            </div>
          </div>
          
          <div className="form-group mb-8">
            <label className="form-label">Password</label>
            <div style={{ position: 'relative' }}>
              <div style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}>
                <Lock size={18} />
              </div>
              <input 
                type="password" 
                className="form-input"
                style={{ paddingLeft: '2.5rem' }} 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required 
              />
            </div>
          </div>
          
          <button type="submit" className="btn w-full" disabled={isLoading}>
            {isLoading ? 'Authenticating...' : (
              <>Sign In <ArrowRight size={18} /></>
            )}
          </button>
        </form>
        
        <div style={{ marginTop: '2rem', padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '0.5rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          <p style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: '0.5rem' }}>Test Accounts (pw: password):</p>
          <ul style={{ paddingLeft: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
            <li>faculty@failsafe.com (Faculty)</li>
            <li>hod@failsafe.com (HOD)</li>
            <li>alice@failsafe.com (Student)</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default Login;
