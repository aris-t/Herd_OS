// components/AddAnimalView.jsx
import React, { useState } from 'react';
import { ChevronLeft } from 'lucide-react';

const AddAnimalView = ({ onBack, onSave }) => {
  const [newAnimal, setNewAnimal] = useState({
    name: '',
    species: '',
    age: '',
    weight: '',
    status: 'Active'
  });

  const handleInputChange = (field, value) => {
    setNewAnimal(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSave = () => {
    onSave(newAnimal);
  };

  const isFormValid = newAnimal.name && newAnimal.species && newAnimal.age && newAnimal.weight;

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
            <h1 className="header-title">Add New Animal</h1>
            <p className="header-subtitle">Enter animal information</p>
          </div>
        </div>
      </div>

      <div className="p-6">
        <div className="max-w-md mx-auto">
          <div className="space-y-6">
            <div className="form-group">
              <label className="form-label">Animal Name</label>
              <input
                type="text"
                value={newAnimal.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className="form-input"
                placeholder="e.g., Mouse A1"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Species</label>
              <select
                value={newAnimal.species}
                onChange={(e) => handleInputChange('species', e.target.value)}
                className="form-select"
              >
                <option value="">Select Species</option>
                <option value="Mus musculus">Mus musculus</option>
                <option value="Rattus rattus">Rattus rattus</option>
                <option value="Rattus norvegicus">Rattus norvegicus</option>
                <option value="Cavia porcellus">Cavia porcellus</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Age</label>
              <input
                type="text"
                value={newAnimal.age}
                onChange={(e) => handleInputChange('age', e.target.value)}
                className="form-input"
                placeholder="e.g., 8 weeks"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Weight</label>
              <input
                type="text"
                value={newAnimal.weight}
                onChange={(e) => handleInputChange('weight', e.target.value)}
                className="form-input"
                placeholder="e.g., 25g"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Status</label>
              <select
                value={newAnimal.status}
                onChange={(e) => handleInputChange('status', e.target.value)}
                className="form-select"
              >
                <option value="Active">Active</option>
                <option value="Rest">Rest</option>
              </select>
            </div>

            <div className="flex space-x-4">
              <button
                onClick={onBack}
                className="btn btn-outline flex-1"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={!isFormValid}
                className={`btn flex-1 ${isFormValid ? 'btn-success' : 'btn-disabled'}`}
              >
                Save Animal
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AddAnimalView;