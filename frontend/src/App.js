import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw, Play, Square, FileText, Settings, Monitor, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import './App.css';

const DeviceConfigFrontend = () => {
  const [deviceStatus, setDeviceStatus] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [config, setConfig] = useState({
    name: '',
    stream_fps: '',
    enabled: false,
    camera_endpoint: ''
  });

  const apiCall = async (endpoint, method = 'GET', body = null) => {
    try {
      setError('');
      setLoading(true);
      
      const response = await fetch(endpoint, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: body ? JSON.stringify(body) : null,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const fetchStatus = useCallback(async () => {
    try {
      const status = await apiCall('/status');
      setDeviceStatus(status);
      setConfig({
        name: status.name || '',
        stream_fps: status.stream_fps || '',
        enabled: status.enabled || false,
        camera_endpoint: status.camera_endpoint || ''
      });
    } catch (err) {
      console.error('Failed to fetch status:', err);
    }
  }, []);

  // Auto-refresh status every 10 seconds
  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const fetchLogs = async () => {
    try {
      const logsData = await apiCall('/logs');
      setLogs(Array.isArray(logsData) ? logsData : []);
    } catch (err) {
      console.error('Failed to fetch logs:', err);
    }
  };

  const handleCommand = async (endpoint, successMessage, body = null) => {
    try {
      await apiCall(endpoint, 'POST', body);
      setSuccess(successMessage);
      setTimeout(() => setSuccess(''), 3000);
      if (endpoint !== '/restart') {
        fetchStatus();
      }
    } catch (err) {
      console.error(`Command failed:`, err);
    }
  };

  const formatUptime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours}h ${minutes}m ${secs}s`;
  };

  return (
    <div className="app">
      <div className="container">
        {/* Header */}
        <div className="header">
          <div className="header-content">
            <div className="header-info">
              <Monitor size={32} />
              <div>
                <h1>Device Control Panel</h1>
                <p>Manage your device configuration and monitoring</p>
              </div>
            </div>
            <button
              onClick={fetchStatus}
              disabled={loading}
              className="btn btn-primary"
            >
              <RefreshCw size={16} className={loading ? 'spinning' : ''} />
              Refresh
            </button>
          </div>
        </div>

        {/* Status Messages */}
        {error && (
          <div className="alert alert-error">
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="alert alert-success">
            <CheckCircle size={20} />
            <span>{success}</span>
          </div>
        )}

        {/* Device Status */}
        {deviceStatus && (
          <div className="card">
            <h2>
              <Settings size={20} />
              Device Status
            </h2>
            <div className="status-grid">
              <div className="status-item">
                <div className="status-label">Device ID</div>
                <div className="status-value">{deviceStatus.device_id}</div>
              </div>
              <div className="status-item">
                <div className="status-label">Name</div>
                <div className="status-value">{deviceStatus.name || 'Unnamed'}</div>
              </div>
              <div className="status-item">
                <div className="status-label">Stream FPS</div>
                <div className="status-value">{deviceStatus.stream_fps}</div>
              </div>
              <div className="status-item">
                <div className="status-label">
                  <Clock size={16} />
                  Uptime
                </div>
                <div className="status-value">{formatUptime(deviceStatus.uptime_sec)}</div>
              </div>
            </div>
            {deviceStatus.camera_endpoint && (
              <div className="endpoint-info">
                <div className="status-label">Camera Endpoint</div>
                <div className="endpoint-value">{deviceStatus.camera_endpoint}</div>
              </div>
            )}
          </div>
        )}

        <div className="grid">
          {/* Configuration Panel */}
          <div className="card">
            <h2>Configuration</h2>
            <div className="form">
              <div className="form-group">
                <label>Device Name</label>
                <input
                  type="text"
                  value={config.name}
                  onChange={(e) => setConfig({...config, name: e.target.value})}
                  placeholder="Enter device name"
                />
              </div>
              <div className="form-group">
                <label>Stream FPS</label>
                <input
                  type="number"
                  value={config.stream_fps}
                  onChange={(e) => setConfig({...config, stream_fps: parseInt(e.target.value) || ''})}
                  placeholder="Enter FPS"
                />
              </div>
              <div className="form-group">
                <label>Camera Endpoint</label>
                <input
                  type="text"
                  value={config.camera_endpoint}
                  onChange={(e) => setConfig({...config, camera_endpoint: e.target.value})}
                  placeholder="Enter camera endpoint URL"
                />
              </div>
              <div className="checkbox-group">
                <input
                  type="checkbox"
                  checked={config.enabled}
                  onChange={(e) => setConfig({...config, enabled: e.target.checked})}
                />
                <label>Enabled</label>
              </div>
              <button
                onClick={() => handleCommand('/rename', 'Device renamed successfully!', { name: config.name })}
                disabled={loading}
                className="btn btn-primary btn-full"
              >
                Update Name
              </button>
            </div>
          </div>

          {/* Control Panel */}
          <div className="card">
            <h2>Device Controls</h2>
            <div className="controls">
              <button
                onClick={() => handleCommand('/start_trial', 'Trial started successfully!', config)}
                disabled={loading}
                className="btn btn-success btn-full"
              >
                <Play size={16} />
                Start Trial
              </button>
              <button
                onClick={() => handleCommand('/stop_trial', 'Trial stopped successfully!')}
                disabled={loading}
                className="btn btn-danger btn-full"
              >
                <Square size={16} />
                Stop Trial
              </button>
              <button
                onClick={() => handleCommand('/files', 'File listing initiated!')}
                disabled={loading}
                className="btn btn-purple btn-full"
              >
                <FileText size={16} />
                List Files
              </button>
              <button
                onClick={() => handleCommand('/restart', 'Device restart initiated!')}
                disabled={loading}
                className="btn btn-warning btn-full"
              >
                <RefreshCw size={16} />
                Restart Device
              </button>
            </div>
          </div>
        </div>

        {/* Logs Panel */}
        <div className="card">
          <div className="logs-header">
            <h2>Device Logs</h2>
            <button
              onClick={fetchLogs}
              disabled={loading}
              className="btn btn-secondary"
            >
              Load Logs
            </button>
          </div>
          <div className="logs-container">
            {logs.length === 0 ? (
              <div className="no-logs">No logs loaded. Click "Load Logs" to fetch device logs.</div>
            ) : (
              <div className="logs">
                {logs.map((log, index) => (
                  <div key={index} className="log-entry">
                    {log.error ? (
                      <span className="log-error">Error: {log.error} - {log.raw}</span>
                    ) : (
                      <>
                        <span className="log-time">[{log.time}]</span>
                        <span className={`log-level log-level-${log.level?.toLowerCase()}`}>{log.level}</span>
                        <span className="log-message">{log.msg}</span>
                      </>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeviceConfigFrontend;