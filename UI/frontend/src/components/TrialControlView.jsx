// components/TrialControlView.jsx
import React, { useState } from 'react';
import { ChevronLeft } from 'lucide-react';
import TrialReady from './trial-steps/TrialReady';
import TrialConfirmation from './trial-steps/TrialConfirmation';
import TrialRunning from './trial-steps/TrialRunning';
import TrialReview from './trial-steps/TrialReview';

const TrialControlView = ({ animal, trial, onBack }) => {
  const [trialStep, setTrialStep] = useState('ready');
  const [trialStatus, setTrialStatus] = useState('stopped');
  const [touchedFields, setTouchedFields] = useState({
    participantId: false,
    trialType: false,
    duration: false,
    conditions: false,
    consent: false
  });

  const handleStartTrial = () => {
    setTrialStep('confirmation');
  };

  const handleReviewTrial = () => {
    setTrialStep('review');  // ← This is what was missing!
  };

  const handleConfirmStart = () => {
    setTrialStep('running');
    setTrialStatus('running');
  };

  const handleStopTrial = () => {
    // Instead of going back to ready, go to review
    setTrialStep('review');
    setTrialStatus('completed');
  };

  const handleCompleteReview = () => {
    // Reset everything and go back to ready state
    setTrialStep('ready');
    setTrialStatus('stopped');
    setTouchedFields({
      participantId: false,
      trialType: false,
      duration: false,
      conditions: false,
      consent: false
    });
  };

  const handleFieldTouch = (fieldKey) => {
    setTouchedFields(prev => ({
      ...prev,
      [fieldKey]: true
    }));
  };

  const handleBackToReady = () => {
    setTrialStep('ready');
    setTouchedFields({
      participantId: false,
      trialType: false,
      duration: false,
      conditions: false,
      consent: false
    });
  };

  const toggleTrialStatus = () => {
    if (trialStatus === 'stopped') {
      setTrialStatus('running');
    } else if (trialStatus === 'running') {
      setTrialStatus('paused');
    } else {
      setTrialStatus('running');
    }
  };

  const handleExportResults = () => {
    // Handle export functionality
    console.log('Exporting trial results...');
    // You could implement actual export logic here
  };

  if (!animal || !trial) return null;

  // If we're in the review step, render the full-screen review component
  if (trialStep === 'review') {
    return (
      <TrialReview
        animal={animal}
        trial={trial}
        onBack={handleCompleteReview}
        onExport={handleExportResults}
      />
    );
  }

  // Otherwise, render the normal trial control flow
  return (
    <div className="bg-white h-full">
      <div className="header">
        <div className="header-content">
          <button
            onClick={onBack}
            className="back-button"
          >
            <ChevronLeft className="w-5 h-5 text-gray-600" />
          </button>
          <div className="flex-1">
            <h1 className="header-title">{trial.name}</h1>
            <p className="header-subtitle">{animal.name}</p>
          </div>
        </div>
      </div>

      <div className="p-6">
        {trialStep === 'ready' && (
          <TrialReady
            animal={animal}
            trial={trial}
            onStartTrial={handleStartTrial}
            onReviewTrial={handleReviewTrial}
          />
        )}

        {trialStep === 'confirmation' && (
          <TrialConfirmation
            animal={animal}
            trial={trial}
            touchedFields={touchedFields}
            onFieldTouch={handleFieldTouch}
            onBack={handleBackToReady}
            onConfirmStart={handleConfirmStart}
          />
        )}

        {trialStep === 'running' && (
          <TrialRunning
            animal={animal}
            trial={trial}
            trialStatus={trialStatus}
            onToggleStatus={toggleTrialStatus}
            onStopTrial={handleStopTrial}
          />
        )}
      </div>
    </div>
  );
};

export default TrialControlView;