// components/trial-steps/TrialConfirmation.jsx
import React from 'react';
import { Play, ArrowLeft, CheckCircle } from 'lucide-react';

const TrialConfirmation = ({ animal, trial, touchedFields, onFieldTouch, onBack, onConfirmStart }) => {
  const requiredFields = [
    { key: 'participantId', label: 'Animal ID', value: animal?.name || '' },
    { key: 'trialType', label: 'Trial Type', value: trial?.name || '' },
    { key: 'conditions', label: 'Environmental Conditions', value: 'Quiet room, normal lighting' },
    { key: 'materials', label: 'Materials', value: 'Test apparatus, data sheets' }
  ];

  const allFieldsTouched = requiredFields.every(field => touchedFields[field.key]);
  const untouchedCount = requiredFields.filter(field => !touchedFields[field.key]).length;

  return (
    <div className="max-w-md mx-auto">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Confirm Trial Details</h2>
        <p className="text-gray-600">Please review and touch each field to confirm</p>
      </div>

      <div className="space-y-3 mb-6">
        {requiredFields.map((field) => (
          <div
            key={field.key}
            onClick={() => onFieldTouch(field.key)}
            className={`confirmation-field ${touchedFields[field.key] ? 'touched' : ''}`}
          >
            <div className="confirmation-field-content">
              <div>
                <p className="confirmation-field-label">{field.label}</p>
                <p className="confirmation-field-value">{field.value}</p>
              </div>
              {touchedFields[field.key] && (
                <CheckCircle className="h-5 w-5 text-green-600" />
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="flex space-x-3">
        <button
          onClick={onBack}
          className="btn btn-secondary flex-1"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </button>
        <button
          onClick={onConfirmStart}
          disabled={!allFieldsTouched}
          className={`btn flex-2 ${
            allFieldsTouched ? 'btn-success' : 'btn-disabled'
          }`}
        >
          <Play className="h-5 w-5" />
          {allFieldsTouched ? 'Start Trial' : `Touch ${untouchedCount} more fields`}
        </button>
      </div>
    </div>
  );
};

export default TrialConfirmation;