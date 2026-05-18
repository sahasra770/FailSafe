import React, { useState, useRef } from 'react';
import { studentAPI } from '../api/axios';
import './UploadData.css';

const RISK_COLOR = { High: '#ef4444', Medium: '#f59e0b', Low: '#22c55e' };
const RISK_BG    = { High: '#fef2f2', Medium: '#fffbeb', Low: '#f0fdf4' };

export default function UploadData() {
  const [file,     setFile]     = useState(null);
  const [status,   setStatus]   = useState('idle'); // idle | loading | success | error
  const [message,  setMessage]  = useState('');
  const [results,  setResults]  = useState(null);
  const [preview,  setPreview]  = useState([]);
  const inputRef = useRef();

  // ── file selection ─────────────────────────────────────────────────────────
  const handleFile = (f) => {
    if (!f || !f.name.endsWith('.csv')) {
      setMessage('Please select a .csv file.');
      setStatus('error');
      return;
    }
    setFile(f);
    setStatus('idle');
    setMessage('');
    setResults(null);

    // Show first 4 rows as preview
    const reader = new FileReader();
    reader.onload = (e) => {
      const lines = e.target.result.split('\n').filter(Boolean).slice(0, 4);
      setPreview(lines);
    };
    reader.readAsText(f);
  };

  const onInputChange = (e) => handleFile(e.target.files[0]);

  const onDrop = (e) => {
    e.preventDefault();
    handleFile(e.dataTransfer.files[0]);
  };

  // ── upload ─────────────────────────────────────────────────────────────────
  const handleUpload = async () => {
    if (!file) return;
    setStatus('loading');
    setMessage('');
    try {
      const data = await studentAPI.uploadCSV(file);
      setResults(data);
      setStatus('success');
      setMessage(`✅ ${data.students_processed} students processed successfully.`);
    } catch (err) {
      setStatus('error');
      setMessage(
        err?.response?.data?.detail ||
        'Upload failed. Check that the CSV has the required columns.'
      );
    }
  };

  const reset = () => {
    setFile(null); setStatus('idle');
    setMessage(''); setResults(null); setPreview([]);
    if (inputRef.current) inputRef.current.value = '';
  };

  // ── render ─────────────────────────────────────────────────────────────────
  return (
    <div className="upload-page">
      <div className="upload-header">
        <h1>Upload Student Data</h1>
        <p>Upload a CSV file to run AI risk predictions on all students at once.</p>
      </div>

      {/* Drop zone */}
      <div
        className={`drop-zone ${file ? 'has-file' : ''}`}
        onDragOver={(e) => e.preventDefault()}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          onChange={onInputChange}
          style={{ display: 'none' }}
        />
        {file ? (
          <div className="file-info">
            <span className="file-icon">📄</span>
            <span className="file-name">{file.name}</span>
            <span className="file-size">({(file.size / 1024).toFixed(1)} KB)</span>
          </div>
        ) : (
          <div className="drop-prompt">
            <span className="drop-icon">☁️</span>
            <p>Drag & drop your CSV here, or <strong>click to browse</strong></p>
          </div>
        )}
      </div>

      {/* CSV preview */}
      {preview.length > 0 && (
        <div className="csv-preview">
          <p className="preview-label">Preview (first 3 rows):</p>
          <div className="preview-table-wrap">
            <table className="preview-table">
              <thead>
                <tr>
                  {preview[0].split(',').map((h, i) => <th key={i}>{h.trim()}</th>)}
                </tr>
              </thead>
              <tbody>
                {preview.slice(1).map((row, r) => (
                  <tr key={r}>
                    {row.split(',').map((cell, c) => <td key={c}>{cell.trim()}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Action buttons */}
      <div className="upload-actions">
        <button
          className="btn-upload"
          onClick={handleUpload}
          disabled={!file || status === 'loading'}
        >
          {status === 'loading' ? '⏳ Analysing…' : '🚀 Run Predictions'}
        </button>
        {file && (
          <button className="btn-reset" onClick={reset}>✕ Clear</button>
        )}
      </div>

      {/* Status message */}
      {message && (
        <p className={`status-msg ${status}`}>{message}</p>
      )}

      {/* Results */}
      {results && (
        <div className="results-section">
          {/* Summary cards */}
          <div className="summary-cards">
            {['High', 'Medium', 'Low'].map((level) => (
              <div
                key={level}
                className="summary-card"
                style={{ borderColor: RISK_COLOR[level], background: RISK_BG[level] }}
              >
                <span className="summary-count" style={{ color: RISK_COLOR[level] }}>
                  {results.summary[level]}
                </span>
                <span className="summary-label">{level} Risk</span>
              </div>
            ))}
          </div>

          {/* Per-student table */}
          <div className="results-table-wrap">
            <table className="results-table">
              <thead>
                <tr>
                  <th>Student ID</th>
                  <th>Risk Level</th>
                  <th>Confidence</th>
                  <th>Low %</th>
                  <th>Medium %</th>
                  <th>High %</th>
                </tr>
              </thead>
              <tbody>
                {results.predictions.map((s, i) => (
                  <tr key={i}>
                    <td>{s.student_id}</td>
                    <td>
                      <span
                        className="risk-badge"
                        style={{
                          background: RISK_BG[s.risk_label],
                          color: RISK_COLOR[s.risk_label],
                          border: `1px solid ${RISK_COLOR[s.risk_label]}`
                        }}
                      >
                        {s.risk_label}
                      </span>
                    </td>
                    <td>{s.risk_score}%</td>
                    <td style={{ color: RISK_COLOR.Low }}>{s.probabilities.Low}%</td>
                    <td style={{ color: RISK_COLOR.Medium }}>{s.probabilities.Medium}%</td>
                    <td style={{ color: RISK_COLOR.High }}>{s.probabilities.High}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Expected format hint */}
      <div className="format-hint">
        <h3>📋 Expected CSV Columns</h3>
        <p><strong>Required:</strong> G1, G2, absences, failures, studytime</p>
        <p><strong>Optional (improves accuracy):</strong> Medu, Fedu, goout, Dalc, Walc, health, famrel, freetime, traveltime, age</p>
        <p><strong>For identification:</strong> student_id or name</p>
      </div>
    </div>
  );
}
