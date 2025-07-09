// components/AnimalsListView.jsx
import React from 'react';
import { Plus, User } from 'lucide-react';
import { getStatusColor } from '../utils/statusUtils';

const AnimalsListView = ({ animals, onAnimalSelect, onAddAnimal }) => {
  return (
    <div className="bg-white h-full">
      <div className="header">
        <h1 className="header-title">Research Animals</h1>
        <div className="flex items-center justify-between">
          <p className="header-subtitle">Select an animal to view details and trials</p>
          <button 
            onClick={onAddAnimal}
            className="btn btn-success"
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
              onClick={() => onAnimalSelect(animal)}
              className="card"
            >
              <div className="card-content">
                <div className="card-left">
                  <div className="card-icon">
                    <User className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="card-title">{animal.name}</h3>
                    <p className="card-subtitle">{animal.species}</p>
                  </div>
                </div>
                <div className="card-right">
                  <span className={`status-badge ${getStatusColor(animal.status)}`}>
                    {animal.status}
                  </span>
                  <p className="card-meta">{animal.age} • {animal.weight}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AnimalsListView;