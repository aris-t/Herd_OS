// components/AnimalDetailView.jsx
import React from 'react';
import { ChevronLeft, Plus, Settings, Activity, Calendar, Clock } from 'lucide-react';
import { getStatusColor } from '../utils/statusUtils';
import { samplePassives } from '../data/sampleData';

const AnimalDetailView = ({ animal, trials, onBack, onTrialSelect, onTrialReview }) => {
    if (!animal) return null;

    const passives = samplePassives[animal.id] || [];

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
                        <h1 className="header-title">{animal.name}</h1>
                        <p className="header-subtitle">{animal.species}</p>
                    </div>
                    <button className="back-button">
                        <Settings className="w-5 h-5 text-gray-600" />
                    </button>
                </div>
            </div>

            <div className="p-6">
                {/* Animal Info */}
                <div className="info-panel">
                    <div className="flex items-center justify-between">
                        <h2 className="info-panel-title">Animal Information</h2>
                        <button
                            className="btn btn-secondary flex items-center gap-1"
                            onClick={() => {
                                if (typeof animal.onEdit === 'function') animal.onEdit(animal);
                            }}
                            aria-label="Edit animal details"
                        >
                            <svg
                                className="w-4 h-4"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth={2}
                                viewBox="0 0 24 24"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    d="M15.232 5.232l3.536 3.536M9 13l6.586-6.586a2 2 0 112.828 2.828L11.828 15.828a2 2 0 01-1.414.586H7v-3a2 2 0 01.586-1.414z"
                                />
                            </svg>
                            <span>Edit</span>
                        </button>
                    </div>
                    <div className="info-grid">
                        <div>
                            <p className="info-item-label">Age</p>
                            <p className="info-item-value">{animal.age}</p>
                        </div>
                        <div>
                            <p className="info-item-label">Weight</p>
                            <p className="info-item-value">{animal.weight}</p>
                        </div>
                        <div>
                            <p className="info-item-label">Status</p>
                            <span className={`status-badge ${getStatusColor(animal.status)}`}>
                                {animal.status}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Trials Section */}
                <div className="flex items-center justify-between mb-4">
                    <h2 className="font-semibold text-gray-800">Trials</h2>
                    <button className="btn btn-primary">
                        <Plus className="w-4 h-4" />
                        <span>Add Trial</span>
                    </button>
                </div>

                <div className="space-y-3">
                    {trials.map((trial) => (
                        <div
                            key={trial.id}
                            onClick={() => {
                                if (trial.status === 'completed') {
                                    // Route to review - you'll need to pass this as a prop
                                    onTrialReview(trial);
                                } else {
                                    // Route to trial control (start chain)
                                    onTrialSelect(trial);
                                }
                            }}
                            className="card"
                        >
                            <div className="card-content">
                                <div className="card-left">
                                    <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                                        <Activity className="w-4 h-4 text-purple-600" />
                                    </div>
                                    <div>
                                        <h3 className="card-title">{trial.name}</h3>
                                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                                            <div className="flex items-center space-x-1">
                                                <Calendar className="w-3 h-3" />
                                                <span>{trial.date}</span>
                                            </div>
                                            <div className="flex items-center space-x-1">
                                                <Clock className="w-3 h-3" />
                                                <span>{trial.duration}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <span className={`status-badge ${getStatusColor(trial.status)}`}>
                                    {trial.status}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Passives Section */}
                <div className="flex items-center justify-between mt-8 mb-4">
                    <h2 className="font-semibold text-gray-800">Passives</h2>
                    <button className="btn btn-primary">
                        <Plus className="w-4 h-4" />
                        <span>Add Passive</span>
                    </button>
                </div>

                <div className="space-y-3">
                    {passives.length > 0 ? (
                        passives.map((passive) => (
                            <div
                                key={passive.id}
                                className="card"
                            >
                                <div className="card-content">
                                    <div className="card-left">
                                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                                            <Activity className="w-4 h-4 text-blue-600" />
                                        </div>
                                        <div>
                                            <h3 className="card-title">{passive.name}</h3>
                                            <div className="flex items-center space-x-4 text-sm text-gray-600">
                                                <div className="flex items-center space-x-1">
                                                    <Calendar className="w-3 h-3" />
                                                    <span>{passive.date}</span>
                                                </div>
                                                <div className="flex items-center space-x-1">
                                                    <Clock className="w-3 h-3" />
                                                    <span>{passive.duration}</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <span className={`status-badge ${getStatusColor(passive.status)}`}>
                                        {passive.status}
                                    </span>
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="text-gray-500 text-sm">No passives found.</div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AnimalDetailView;