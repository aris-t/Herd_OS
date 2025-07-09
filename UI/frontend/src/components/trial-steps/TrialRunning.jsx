// components/trial-steps/TrialRunning.jsx
import React from 'react';
import { Play, Pause, Square } from 'lucide-react';

const TrialRunning = ({ animal, trial, trialStatus, onToggleStatus, onStopTrial }) => {
  return (
    <div className="max-w-md mx-auto">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-green-700 mb-2">Trial in Progress</h2>
        <p className="text-gray-600">Session is currently running</p>
      </div>

      <div className="space-y-4 mb-6">
        <div className="alert alert-success">
          <div className="alert-header">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
            <span>Active Session</span>
          </div>
          <div className="text-sm text-green-700 space-y-1">
            <p><span className="font-medium">Animal:</span> {animal.name}</p>
            <p><span className="font-medium">Trial Type:</span> {trial.name}</p>
            <p><span className="font-medium">Started:</span> {new Date().toLocaleTimeString()}</p>
          </div>
        </div>

        <div className="info-panel">
          <h3 className="info-panel-title">Session Progress</h3>
          <div className="progress-bar">
            <div className="progress-fill animated" style={{width: '33%'}}></div>
          </div>
          <p className="text-sm text-gray-600 mt-1">Approximately 15 minutes elapsed</p>
        </div>

        <div className="info-panel">
          <h2 className="info-panel-title">Trial Controls</h2>
          
          <div className={`trial-status-indicator trial-status-${trialStatus}`}>
            <div className={`trial-status-dot ${trialStatus}`}></div>
          </div>

          <div className="text-center mb-6">
            <p className="text-lg font-medium text-gray-800 capitalize">
              {trialStatus === 'running' ? 'Recording Data' : 
               trialStatus === 'paused' ? 'Trial Paused' : 'Trial Stopped'}
            </p>
          </div>

          <div className="flex justify-center space-x-4">
            <button
              onClick={onToggleStatus}
              className={`btn ${
                trialStatus === 'stopped' ? 'btn-success' :
                trialStatus === 'running' ? 'btn-warning' :
                'btn-success'
              }`}
            >
              {trialStatus === 'stopped' ? <Play className="w-4 h-4" /> :
               trialStatus === 'running' ? <Pause className="w-4 h-4" /> :
               <Play className="w-4 h-4" />}
              <span>
                {trialStatus === 'stopped' ? 'Start' :
                 trialStatus === 'running' ? 'Pause' : 'Resume'}
              </span>
            </button>
            
            <button
              onClick={onStopTrial}
              disabled={trialStatus === 'stopped'}
              className={`btn ${
                trialStatus === 'stopped' ? 'btn-disabled' : 'btn-danger'
              }`}
            >
              <Square className="w-4 h-4" />
              <span>Stop</span>
            </button>
          </div>
        </div>
      </div>

      <button
        onClick={onStopTrial}
        className="btn btn-danger btn-full"
      >
        End Trial Session
      </button>
    </div>
  );
};

export default TrialRunning;