import React, { useState } from 'react';
import { Play, AlertCircle, CheckCircle, ArrowLeft } from 'lucide-react';

export default function ResearchTrialPane() {
  const [currentStep, setCurrentStep] = useState('ready'); // 'ready', 'confirmation', 'running'
  const [touchedFields, setTouchedFields] = useState({
    participantId: false,
    trialType: false,
    duration: false,
    conditions: false,
    consent: false
  });

  const requiredFields = [
    { key: 'participantId', label: 'Participant ID', value: 'P-2024-001' },
    { key: 'trialType', label: 'Trial Type', value: 'Cognitive Assessment' },
    { key: 'duration', label: 'Expected Duration', value: '45 minutes' },
    { key: 'conditions', label: 'Environmental Conditions', value: 'Quiet room, normal lighting' },
    { key: 'consent', label: 'Consent Status', value: 'Verified and signed' }
  ];

  const handleFieldTouch = (fieldKey) => {
    setTouchedFields(prev => ({
      ...prev,
      [fieldKey]: true
    }));
  };

  const allFieldsTouched = Object.values(touchedFields).every(touched => touched);

  const handleStartTrial = () => {
    setCurrentStep('confirmation');
  };

  const handleConfirmStart = () => {
    setCurrentStep('running');
  };

  const handleBack = () => {
    setCurrentStep('ready');
    setTouchedFields({
      participantId: false,
      trialType: false,
      duration: false,
      conditions: false,
      consent: false
    });
  };

  const handleStopTrial = () => {
    setCurrentStep('ready');
    setTouchedFields({
      participantId: false,
      trialType: false,
      duration: false,
      conditions: false,
      consent: false
    });
  };

  if (currentStep === 'ready') {
    return (
      <div className="max-w-md mx-auto bg-white rounded-lg shadow-lg p-6">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Research Trial</h2>
          <p className="text-gray-600">Ready to begin new trial session</p>
        </div>

        <div className="space-y-4 mb-6">
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-semibold text-gray-700 mb-2">Current Session</h3>
            <div className="text-sm text-gray-600 space-y-1">
              <p><span className="font-medium">Participant:</span> P-2024-001</p>
              <p><span className="font-medium">Trial Type:</span> Cognitive Assessment</p>
              <p><span className="font-medium">Status:</span> Ready to start</p>
            </div>
          </div>

          <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
            <div className="flex items-center gap-2 mb-2">
              <AlertCircle className="h-4 w-4 text-blue-600" />
              <span className="text-sm font-medium text-blue-800">Pre-trial Checklist</span>
            </div>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>• Equipment calibrated and ready</li>
              <li>• Participant consent verified</li>
              <li>• Environmental conditions optimal</li>
            </ul>
          </div>
        </div>

        <button
          onClick={handleStartTrial}
          className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          <Play className="h-5 w-5" />
          Start Trial
        </button>
      </div>
    );
  }

  if (currentStep === 'confirmation') {
    return (
      <div className="max-w-md mx-auto bg-white rounded-lg shadow-lg p-6">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Confirm Trial Details</h2>
          <p className="text-gray-600">Please review and touch each field to confirm</p>
        </div>

        <div className="space-y-3 mb-6">
          {requiredFields.map((field) => (
            <div
              key={field.key}
              onClick={() => handleFieldTouch(field.key)}
              className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                touchedFields[field.key]
                  ? 'border-green-500 bg-green-50'
                  : 'border-gray-300 bg-gray-50 hover:border-gray-400'
              }`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-700">{field.label}</p>
                  <p className="text-sm text-gray-600">{field.value}</p>
                </div>
                {touchedFields[field.key] && (
                  <CheckCircle className="h-5 w-5 text-green-600" />
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="flex gap-3">
          <button
            onClick={handleBack}
            className="flex-1 bg-gray-500 hover:bg-gray-600 text-white font-semibold py-3 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back
          </button>
          <button
            onClick={handleConfirmStart}
            disabled={!allFieldsTouched}
            className={`flex-2 font-semibold py-3 px-4 rounded-lg transition-colors flex items-center justify-center gap-2 ${
              allFieldsTouched
                ? 'bg-green-600 hover:bg-green-700 text-white'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
          >
            <Play className="h-5 w-5" />
            {allFieldsTouched ? 'Start Trial' : `Touch ${Object.values(touchedFields).filter(t => !t).length} more fields`}
          </button>
        </div>
      </div>
    );
  }

  if (currentStep === 'running') {
    return (
      <div className="max-w-md mx-auto bg-white rounded-lg shadow-lg p-6">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-green-700 mb-2">Trial in Progress</h2>
          <p className="text-gray-600">Session is currently running</p>
        </div>

        <div className="space-y-4 mb-6">
          <div className="bg-green-50 p-4 rounded-lg border border-green-200">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
              <span className="font-medium text-green-800">Active Session</span>
            </div>
            <div className="text-sm text-green-700 space-y-1">
              <p><span className="font-medium">Participant:</span> P-2024-001</p>
              <p><span className="font-medium">Trial Type:</span> Cognitive Assessment</p>
              <p><span className="font-medium">Started:</span> {new Date().toLocaleTimeString()}</p>
            </div>
          </div>

          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-semibold text-gray-700 mb-2">Session Progress</h3>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-blue-600 h-2 rounded-full w-1/3 animate-pulse"></div>
            </div>
            <p className="text-sm text-gray-600 mt-1">Approximately 15 minutes elapsed</p>
          </div>
        </div>

        <button
          onClick={handleStopTrial}
          className="w-full bg-red-600 hover:bg-red-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors"
        >
          Stop Trial
        </button>
      </div>
    );
  }
}