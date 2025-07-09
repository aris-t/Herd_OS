// App.jsx
import React, { useState } from 'react';
import AnimalsListView from './components/AnimalsListView';
import AnimalDetailView from './components/AnimalDetailView';
import AddAnimalView from './components/AddAnimalView';
import TrialControlView from './components/TrialControlView';
import { sampleAnimals, sampleTrials } from './data/sampleData';
import './App.css';

const App = () => {
  const [currentView, setCurrentView] = useState('animals');
  const [selectedAnimal, setSelectedAnimal] = useState(null);
  const [selectedTrial, setSelectedTrial] = useState(null);
  const [animals, setAnimals] = useState(sampleAnimals);

  const handleAnimalSelect = (animal) => {
    setSelectedAnimal(animal);
    setCurrentView('animal-detail');
  };

  const handleTrialSelect = (trial) => {
    setSelectedTrial(trial);
    setCurrentView('trial-control');
  };

  const handleTrialReview = (trial) => {
    setSelectedTrial(trial);
    setCurrentView('trial-control');
  };

  const handleAddAnimal = () => {
    setCurrentView('add-animal');
  };

  const handleSaveAnimal = (newAnimal) => {
    const animal = {
      id: animals.length + 1,
      ...newAnimal
    };
    setAnimals([...animals, animal]);
    setCurrentView('animals');
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
    }
  };

  const getViewClass = (viewName) => {
    let className = 'view-slide-up';
    
    if (currentView === viewName) {
      className += ' active';
    } else {
      // Determine if view is above or below current view
      const viewOrder = ['animals', 'animal-detail', 'trial-control'];
      const currentIndex = viewOrder.indexOf(currentView);
      const viewIndex = viewOrder.indexOf(viewName);
      
      if (viewName === 'add-animal') {
        className += currentView === 'add-animal' ? ' active' : ' below';
      } else if (viewIndex < currentIndex) {
        className += ' above';
      } else {
        className += ' below';
      }
    }
    
    return className;
  };

  return (
    <div className="app-container">
      {/* Add Animal View */}
      <div className={getViewClass('add-animal')}>
        <AddAnimalView 
          onBack={handleBack}
          onSave={handleSaveAnimal}
        />
      </div>

      {/* Animals List View */}
      <div className={getViewClass('animals')}>
        <AnimalsListView
          animals={animals}
          onAnimalSelect={handleAnimalSelect}
          onAddAnimal={handleAddAnimal}
        />
      </div>

      {/* Animal Detail View */}
      <div className={getViewClass('animal-detail')}>
        <AnimalDetailView
          animal={selectedAnimal}
          trials={sampleTrials[selectedAnimal?.id] || []}
          onBack={handleBack}
          onTrialSelect={handleTrialSelect}
        />
      </div>

      {/* Trial Control View */}
      <div className={getViewClass('trial-control')}>
        <TrialControlView
          animal={selectedAnimal}
          trial={selectedTrial}
          onBack={handleBack}
        />
      </div>
    </div>
  );
};

export default App;