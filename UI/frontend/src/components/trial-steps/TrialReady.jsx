// components/trial-steps/TrialReady.jsx
import React from 'react';
import { Play, AlertCircle } from 'lucide-react';

const TrialReady = ({ animal, trial, onStartTrial, onReviewTrial }) => {
  const isCompleted = trial.status === 'Completed';

  return (
    <div className="max-w-md mx-auto">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Research Trial</h2>
        <p className="text-gray-600">Ready to begin new trial session</p>
      </div>

      <div className="space-y-4 mb-6">
        <div className="info-panel">
          <h3 className="info-panel-title">Current Session</h3>
          <div className="text-sm text-gray-600 space-y-1">
            <p><span className="font-medium">Animal:</span> {animal.name}</p>
            <p><span className="font-medium">Trial Type:</span> {trial.name}</p>
            <p><span className="font-medium">Expected Duration:</span> {trial.duration}</p>
            <p><span className="font-medium">Status:</span> {trial.status}</p>
          </div>
        </div>

        <div className="alert alert-info">
          <div className="alert-header">
            <AlertCircle className="alert-icon" />
            <span>Pre-trial Checklist</span>
          </div>
          <ul className="alert-list">
            <li>Equipment calibrated and ready</li>
            <li>Animal welfare verified</li>
            <li>Environmental conditions optimal</li>
            <li>Protocol requirements met</li>
          </ul>
        </div>
      </div>

      {isCompleted ? (
        <button
          className="btn btn-blue btn-full"
          onClick={onReviewTrial}
        >
          Review
        </button>
      ) : (
        <button
          onClick={onStartTrial}
          className="btn btn-success btn-full"
        >
          <Play className="h-5 w-5" />
          Start Trial
        </button>
      )}
    </div>
  );
};

export default TrialReady;