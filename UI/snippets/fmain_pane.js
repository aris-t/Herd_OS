import React, { useState } from 'react';
import { ChevronLeft, Plus, Play, Pause, Square, Settings, User, Calendar, Clock, Activity } from 'lucide-react';

const ResearchAnimalUI = () => {
  const [currentView, setCurrentView] = useState('animals');
  const [selectedAnimal, setSelectedAnimal] = useState(null);
  const [selectedTrial, setSelectedTrial] = useState(null);
  const [trialStatus, setTrialStatus] = useState('stopped');
  const [newAnimal, setNewAnimal] = useState({
    name: '',
    species: '',
    age: '',
    weight: '',
    status: 'Active'
  });

  // Sample data
  const animals = [
    { id: 1, name: 'Mouse A1', species: 'Mus musculus', age: '8 weeks', weight: '25g', status: 'Active' },
    { id: 2, name: 'Mouse B2', species: 'Mus musculus', age: '10 weeks', weight: '28g', status: 'Active' },
    { id: 3, name: 'Rat C3', species: 'Rattus rattus', age: '12 weeks', weight: '180g', status: 'Active' },
    { id: 4, name: 'Mouse D4', species: 'Mus musculus', age: '9 weeks', weight: '26g', status: 'Rest' },
    { id: 5, name: 'Rat E5', species: 'Rattus rattus', age: '14 weeks', weight: '195g', status: 'Active' },
  ];

  const trials = {
    1: [
      { id: 101, name: 'Behavioral Test A', date: '2024-07-05', duration: '30 min', status: 'Completed' },
      { id: 102, name: 'Cognitive Assessment', date: '2024-07-07', duration: '45 min', status: 'Completed' },
      { id: 103, name: 'Motor Function Test', date: '2024-07-08', duration: '25 min', status: 'Pending' },
    ],
    2: [
      { id: 201, name: 'Memory Test B', date: '2024-07-06', duration: '35 min', status: 'Completed' },
      { id: 202, name: 'Social Behavior', date: '2024-07-08', duration: '60 min', status: 'In Progress' },
    ],
    3: [
      { id: 301, name: 'Maze Navigation', date: '2024-07-04', duration: '40 min', status: 'Completed' },
      { id: 302, name: 'Fear Conditioning', date: '2024-07-07', duration: '50 min', status: 'Completed' },
      { id: 303, name: 'Novel Object Test', date: '2024-07-08', duration: '20 min', status: 'Pending' },
    ],
    4: [
      { id: 401, name: 'Stress Response', date: '2024-07-03', duration: '30 min', status: 'Completed' },
    ],
    5: [
      { id: 501, name: 'Spatial Memory', date: '2024-07-05', duration: '45 min', status: 'Completed' },
      { id: 502, name: 'Attention Test', date: '2024-07-08', duration: '35 min', status: 'In Progress' },
    ],
  };

  const handleAnimalSelect = (animal) => {
    setSelectedAnimal(animal);
    setCurrentView('animal-detail');
  };

  const handleTrialSelect = (trial) => {
    setSelectedTrial(trial);
    setCurrentView('trial-control');
  };

  const handleBack = () => {
    if (currentView === 'trial-control') {
      setCurrentView('animal-detail');
      setSelectedTrial(null);
    } else if (currentView === 'animal-detail') {
      setCurrentView('animals');
      setSelectedAnimal(null);
    } else if (currentView === 'add-animal') {
      setCurrentView('animals');
      setNewAnimal({
        name: '',
        species: '',
        age: '',
        weight: '',
        status: 'Active'
      });
    }
  };

  const handleAddAnimal = () => {
    setCurrentView('add-animal');
  };

  const handleSaveAnimal = () => {
    // In a real app, this would save to a database
    console.log('Saving animal:', newAnimal);
    setCurrentView('animals');
    setNewAnimal({
      name: '',
      species: '',
      age: '',
      weight: '',
      status: 'Active'
    });
  };

  const handleInputChange = (field, value) => {
    setNewAnimal(prev => ({
      ...prev,
      [field]: value
    }));
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

  const stopTrial = () => {
    setTrialStatus('stopped');
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Active': return 'bg-green-100 text-green-800';
      case 'Rest': return 'bg-yellow-100 text-yellow-800';
      case 'Completed': return 'bg-blue-100 text-blue-800';
      case 'In Progress': return 'bg-purple-100 text-purple-800';
      case 'Pending': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 relative overflow-hidden">
      {/* Add Animal View */}
      <div className={`absolute inset-0 transition-transform duration-300 ease-in-out ${
        currentView === 'add-animal' ? 'translate-y-0' : 'translate-y-full'
      }`}>
        <div className="bg-white h-full">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center space-x-4">
              <button
                onClick={handleBack}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <ChevronLeft className="w-5 h-5 text-gray-600" />
              </button>
              <div className="flex-1">
                <h1 className="text-2xl font-bold text-gray-800">Add New Animal</h1>
                <p className="text-gray-600">Enter animal information</p>
              </div>
            </div>
          </div>

          <div className="p-6">
            <div className="max-w-md mx-auto">
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Animal Name
                  </label>
                  <input
                    type="text"
                    value={newAnimal.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g., Mouse A1"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Species
                  </label>
                  <select
                    value={newAnimal.species}
                    onChange={(e) => handleInputChange('species', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Select Species</option>
                    <option value="Mus musculus">Mus musculus</option>
                    <option value="Rattus rattus">Rattus rattus</option>
                    <option value="Rattus norvegicus">Rattus norvegicus</option>
                    <option value="Cavia porcellus">Cavia porcellus</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Age
                  </label>
                  <input
                    type="text"
                    value={newAnimal.age}
                    onChange={(e) => handleInputChange('age', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g., 8 weeks"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Weight
                  </label>
                  <input
                    type="text"
                    value={newAnimal.weight}
                    onChange={(e) => handleInputChange('weight', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g., 25g"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Status
                  </label>
                  <select
                    value={newAnimal.status}
                    onChange={(e) => handleInputChange('status', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="Active">Active</option>
                    <option value="Rest">Rest</option>
                  </select>
                </div>

                <div className="flex space-x-4 pt-4">
                  <button
                    onClick={handleBack}
                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveAnimal}
                    disabled={!newAnimal.name || !newAnimal.species || !newAnimal.age || !newAnimal.weight}
                    className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                  >
                    Save Animal
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Animals List View */}
      <div className={`absolute inset-0 transition-transform duration-300 ease-in-out ${
        currentView === 'animals' ? 'translate-y-0' : '-translate-y-full'
      }`}>
        <div className="bg-white h-full">
          <div className="p-6 border-b border-gray-200">
            <h1 className="text-2xl font-bold text-gray-800 mb-2">Research Animals</h1>
            <div className="flex items-center justify-between">
              <p className="text-gray-600">Select an animal to view details and trials</p>
              <button 
                onClick={handleAddAnimal}
                className="flex items-center space-x-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
              >
                <Plus className="w-4 h-4" />
                <span>Add Animal</span>
              </button>
            </div>
          </div>
          
          <div className="p-6">
            <div className="space-y-4">
              {animals.map((animal) => (
                <div
                  key={animal.id}
                  onClick={() => handleAnimalSelect(animal)}
                  className="bg-white border border-gray-200 rounded-lg p-4 cursor-pointer hover:shadow-md transition-shadow"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                        <User className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-800">{animal.name}</h3>
                        <p className="text-sm text-gray-600">{animal.species}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(animal.status)}`}>
                        {animal.status}
                      </span>
                      <p className="text-xs text-gray-500 mt-1">{animal.age} • {animal.weight}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Animal Detail View */}
      <div className={`absolute inset-0 transition-transform duration-300 ease-in-out ${
        currentView === 'animal-detail' ? 'translate-y-0' : currentView === 'animals' ? 'translate-y-full' : '-translate-y-full'
      }`}>
        <div className="bg-white h-full">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center space-x-4">
              <button
                onClick={handleBack}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <ChevronLeft className="w-5 h-5 text-gray-600" />
              </button>
              <div className="flex-1">
                <h1 className="text-2xl font-bold text-gray-800">
                  {selectedAnimal?.name}
                </h1>
                <p className="text-gray-600">{selectedAnimal?.species}</p>
              </div>
              <button className="p-2 hover:bg-gray-100 rounded-full transition-colors">
                <Settings className="w-5 h-5 text-gray-600" />
              </button>
            </div>
          </div>

          <div className="p-6">
            {/* Animal Info */}
            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <h2 className="font-semibold text-gray-800 mb-3">Animal Information</h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Age</p>
                  <p className="font-medium">{selectedAnimal?.age}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Weight</p>
                  <p className="font-medium">{selectedAnimal?.weight}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Status</p>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(selectedAnimal?.status)}`}>
                    {selectedAnimal?.status}
                  </span>
                </div>
              </div>
            </div>

            {/* Trials Section */}
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-gray-800">Trials</h2>
              <button className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                <Plus className="w-4 h-4" />
                <span>Add Trial</span>
              </button>
            </div>

            <div className="space-y-3">
              {trials[selectedAnimal?.id]?.map((trial) => (
                <div
                  key={trial.id}
                  onClick={() => handleTrialSelect(trial)}
                  className="bg-white border border-gray-200 rounded-lg p-4 cursor-pointer hover:shadow-md transition-shadow"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                        <Activity className="w-4 h-4 text-purple-600" />
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-800">{trial.name}</h3>
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
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(trial.status)}`}>
                      {trial.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Trial Control View */}
      <div className={`absolute inset-0 transition-transform duration-300 ease-in-out ${
        currentView === 'trial-control' ? 'translate-y-0' : 'translate-y-full'
      }`}>
        <div className="bg-white h-full">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center space-x-4">
              <button
                onClick={handleBack}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <ChevronLeft className="w-5 h-5 text-gray-600" />
              </button>
              <div className="flex-1">
                <h1 className="text-2xl font-bold text-gray-800">
                  {selectedTrial?.name}
                </h1>
                <p className="text-gray-600">{selectedAnimal?.name}</p>
              </div>
            </div>
          </div>

          <div className="p-6">
            {/* Trial Info */}
            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <h2 className="font-semibold text-gray-800 mb-3">Trial Information</h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Date</p>
                  <p className="font-medium">{selectedTrial?.date}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Duration</p>
                  <p className="font-medium">{selectedTrial?.duration}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Status</p>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(selectedTrial?.status)}`}>
                    {selectedTrial?.status}
                  </span>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Animal</p>
                  <p className="font-medium">{selectedAnimal?.name}</p>
                </div>
              </div>
            </div>

            {/* Trial Controls */}
            <div className="bg-gray-50 rounded-lg p-6">
              <h2 className="font-semibold text-gray-800 mb-4">Trial Controls</h2>
              
              <div className="flex items-center justify-center mb-6">
                <div className={`w-20 h-20 rounded-full flex items-center justify-center ${
                  trialStatus === 'running' ? 'bg-green-100' : 
                  trialStatus === 'paused' ? 'bg-yellow-100' : 'bg-gray-100'
                }`}>
                  {trialStatus === 'running' ? (
                    <div className="w-6 h-6 bg-green-600 rounded-full animate-pulse"></div>
                  ) : trialStatus === 'paused' ? (
                    <div className="w-6 h-6 bg-yellow-600 rounded-full"></div>
                  ) : (
                    <div className="w-6 h-6 bg-gray-400 rounded-full"></div>
                  )}
                </div>
              </div>

              <div className="text-center mb-6">
                <p className="text-lg font-medium text-gray-800 capitalize">
                  {trialStatus === 'running' ? 'Trial Running' : 
                   trialStatus === 'paused' ? 'Trial Paused' : 'Trial Stopped'}
                </p>
                <p className="text-sm text-gray-600">
                  {trialStatus === 'running' ? 'Recording data...' : 
                   trialStatus === 'paused' ? 'Trial temporarily paused' : 'Ready to start'}
                </p>
              </div>

              <div className="flex justify-center space-x-4">
                <button
                  onClick={toggleTrialStatus}
                  className={`flex items-center space-x-2 px-6 py-3 rounded-lg font-medium transition-colors ${
                    trialStatus === 'stopped' ? 'bg-green-600 hover:bg-green-700 text-white' :
                    trialStatus === 'running' ? 'bg-yellow-600 hover:bg-yellow-700 text-white' :
                    'bg-green-600 hover:bg-green-700 text-white'
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
                  onClick={stopTrial}
                  disabled={trialStatus === 'stopped'}
                  className={`flex items-center space-x-2 px-6 py-3 rounded-lg font-medium transition-colors ${
                    trialStatus === 'stopped' ? 'bg-gray-300 text-gray-500 cursor-not-allowed' :
                    'bg-red-600 hover:bg-red-700 text-white'
                  }`}
                >
                  <Square className="w-4 h-4" />
                  <span>Stop</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResearchAnimalUI;