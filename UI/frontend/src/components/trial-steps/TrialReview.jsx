import React, { useState } from 'react';
import { ChevronLeft, Download, Share2, BarChart3, TrendingUp, Clock, Calendar, FileText, Eye } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import './TrialReview.css';

// Gait analysis data
const gaitData = [
  { time: '0s', strideLength: 42, velocity: 1.2, cadence: 105 },
  { time: '10s', strideLength: 44, velocity: 1.3, cadence: 108 },
  { time: '20s', strideLength: 46, velocity: 1.4, cadence: 110 },
  { time: '30s', strideLength: 48, velocity: 1.5, cadence: 112 },
  { time: '40s', strideLength: 50, velocity: 1.6, cadence: 115 },
  { time: '50s', strideLength: 52, velocity: 1.7, cadence: 118 },
  { time: '60s', strideLength: 54, velocity: 1.8, cadence: 120 },
  { time: '70s', strideLength: 56, velocity: 1.9, cadence: 122 },
  { time: '80s', strideLength: 58, velocity: 2.0, cadence: 125 },
  { time: '90s', strideLength: 60, velocity: 2.1, cadence: 128 }
];

const limbMetrics = [
  { limb: 'Front Left', symmetry: 92, groundContact: 0.65, swingPhase: 0.35, stepLength: 58 },
  { limb: 'Front Right', symmetry: 88, groundContact: 0.68, swingPhase: 0.32, stepLength: 56 },
  { limb: 'Rear Left', symmetry: 85, groundContact: 0.72, swingPhase: 0.28, stepLength: 54 },
  { limb: 'Rear Right', symmetry: 90, groundContact: 0.70, swingPhase: 0.30, stepLength: 57 }
];

const TrialReview = ({ animal, trial, onBack, onExport }) => {
  const [activeTab, setActiveTab] = useState('overview');

  const gaitStats = {
    duration: '90 seconds',
    totalStrides: 128,
    avgVelocity: '1.65 m/s',
    avgStrideLength: '51.0 cm',
    avgCadence: '116 steps/min',
    symmetryIndex: '89.2%'
  };

  const TabButton = ({ id, label, icon: Icon }) => (
    <button
      onClick={() => setActiveTab(id)}
      className={`trial-review-tab ${activeTab === id ? 'active' : ''}`}
    >
      <Icon className="icon" />
      <span>{label}</span>
    </button>
  );

  const StatCard = ({ title, value, subtitle, trend, color = 'blue' }) => (
    <div className="trial-review-stat-card">
      <div className="trial-review-stat-card-content">
        <div>
          <p className="trial-review-stat-label">{title}</p>
          <p className={`trial-review-stat-card-value trial-review-trend-${color}`} style={{color: getColorValue(color)}}>{value}</p>
          {subtitle && <p className="trial-review-stat-card-subtitle">{subtitle}</p>}
        </div>
        {trend && (
          <div className={`trial-review-trend trial-review-trend-${color}`}>
            <TrendingUp className="icon" />
            <span>{trend}</span>
          </div>
        )}
      </div>
    </div>
  );

  const getColorValue = (color) => {
    const colors = {
      blue: '#2563eb',
      green: '#059669',
      purple: '#9333ea',
      orange: '#ea580c'
    };
    return colors[color] || colors.blue;
  };

  return (
    <div className="trial-review">
      <div className="trial-review-header">
        <div className="trial-review-header-content">
          <div className="trial-review-header-top">
            <div className="trial-review-header-left">
              <button
                onClick={onBack}
                className="trial-review-back-btn"
              >
                <ChevronLeft className="icon-lg" />
                <span>Back</span>
              </button>
              <div>
                <h1 className="trial-review-title">{trial?.name} - Results</h1>
                <p className="trial-review-subtitle">{animal?.name} • {animal?.species}</p>
              </div>
            </div>
            <div className="trial-review-actions">
              <button 
                onClick={onExport}
                className="trial-review-btn trial-review-btn-primary"
              >
                <Download className="icon" />
                Export Results
              </button>
              <button className="trial-review-btn trial-review-btn-secondary">
                <Share2 className="icon" />
                Share
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="trial-review-content">
        {/* Navigation Tabs */}
        <div className="trial-review-tabs">
          <TabButton id="overview" label="Overview" icon={BarChart3} />
          <TabButton id="performance" label="Performance" icon={TrendingUp} />
          <TabButton id="analysis" label="Analysis" icon={Eye} />
          <TabButton id="notes" label="Notes" icon={FileText} />
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="trial-review-section">
            {/* Gait Summary */}
            <div className="trial-review-card">
              <div className="trial-review-card-header">
                <Calendar className="icon-lg" style={{color: '#6b7280'}} />
                <h2 className="trial-review-card-title">Gait Analysis Summary</h2>
              </div>
              <div className="trial-review-grid trial-review-grid-3">
                <div className="trial-review-stat-item">
                  <Clock className="icon-lg" style={{color: '#2563eb'}} />
                  <div>
                    <p className="trial-review-stat-label">Duration</p>
                    <p className="trial-review-stat-value">{gaitStats.duration}</p>
                  </div>
                </div>
                <div className="trial-review-stat-item">
                  <BarChart3 className="icon-lg" style={{color: '#059669'}} />
                  <div>
                    <p className="trial-review-stat-label">Total Strides</p>
                    <p className="trial-review-stat-value">{gaitStats.totalStrides}</p>
                  </div>
                </div>
                <div className="trial-review-stat-item">
                  <TrendingUp className="icon-lg" style={{color: '#9333ea'}} />
                  <div>
                    <p className="trial-review-stat-label">Avg Velocity</p>
                    <p className="trial-review-stat-value">{gaitStats.avgVelocity}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Stats Grid */}
            <div className="trial-review-grid trial-review-grid-4">
              <StatCard 
                title="Stride Length"
                value={gaitStats.avgStrideLength}
                trend="+8%"
                color="green"
              />
              <StatCard 
                title="Cadence"
                value={gaitStats.avgCadence}
                trend="+12 steps"
                color="blue"
              />
              <StatCard 
                title="Symmetry Index"
                value={gaitStats.symmetryIndex}
                subtitle="improved balance"
                color="purple"
              />
              <StatCard 
                title="Recovery Rate"
                value="85%"
                subtitle="vs pre-surgery"
                trend="+25%"
                color="orange"
              />
            </div>

            {/* Gait Progression Chart */}
            <div className="trial-review-card">
              <h3 className="trial-review-card-title">Gait Parameters Over Time</h3>
              <div className="trial-review-chart">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={gaitData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis yAxisId="left" domain={[0, 70]} />
                    <YAxis yAxisId="right" orientation="right" domain={[0, 3]} />
                    <Tooltip />
                    <Line 
                      yAxisId="left"
                      type="monotone" 
                      dataKey="strideLength" 
                      stroke="#3b82f6" 
                      strokeWidth={2}
                      name="Stride Length (cm)"
                    />
                    <Line 
                      yAxisId="right"
                      type="monotone" 
                      dataKey="velocity" 
                      stroke="#10b981" 
                      strokeWidth={2}
                      name="Velocity (m/s)"
                    />
                    <Line 
                      yAxisId="left"
                      type="monotone" 
                      dataKey="cadence" 
                      stroke="#f59e0b" 
                      strokeWidth={2}
                      name="Cadence (steps/min)"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}

        {/* Performance Tab */}
        {activeTab === 'performance' && (
          <div className="trial-review-section">
            {/* Limb Symmetry Analysis */}
            <div className="trial-review-card">
              <h3 className="trial-review-card-title">Limb Symmetry Analysis</h3>
              <div className="trial-review-chart-small">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={limbMetrics}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="limb" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="symmetry" fill="#3b82f6" name="Symmetry %" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Detailed Metrics */}
            <div className="trial-review-grid trial-review-grid-2">
              <div className="trial-review-card">
                <h3 className="trial-review-card-title">Limb Performance</h3>
                <div>
                  {limbMetrics.map((limb, index) => (
                    <div key={index} className="trial-review-phase-item">
                      <div>
                        <p className="trial-review-phase-name">{limb.limb}</p>
                        <p className="trial-review-phase-attempts">Step: {limb.stepLength}cm | Contact: {limb.groundContact}s</p>
                      </div>
                      <div style={{textAlign: 'right'}}>
                        <p className="trial-review-phase-accuracy">{limb.symmetry}%</p>
                        <p className="trial-review-phase-accuracy-label">symmetry</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="trial-review-card">
                <h3 className="trial-review-card-title">Recovery Insights</h3>
                <div>
                  <div className="trial-review-insight trial-review-insight-green">
                    <p className="trial-review-insight-title">Excellent Progress</p>
                    <p className="trial-review-insight-text">Significant improvement in stride consistency and velocity</p>
                  </div>
                  <div className="trial-review-insight trial-review-insight-blue">
                    <p className="trial-review-insight-title">Gait Stability</p>
                    <p className="trial-review-insight-text">Increased ground contact time indicating better balance</p>
                  </div>
                  <div className="trial-review-insight trial-review-insight-purple">
                    <p className="trial-review-insight-title">Limb Coordination</p>
                    <p className="trial-review-insight-text">89% symmetry index shows good bilateral function</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Analysis Tab */}
        {activeTab === 'analysis' && (
          <div className="trial-review-section">
            <div className="trial-review-card">
              <h3 className="trial-review-card-title">Gait Analysis Metrics</h3>
              <div className="trial-review-grid trial-review-grid-2">
                <div>
                  <h4 style={{fontWeight: '500', color: '#374151', marginBottom: '0.75rem'}}>Temporal Parameters</h4>
                  <div className="trial-review-metrics">
                    <div className="trial-review-metric-row">
                      <span className="trial-review-metric-label">Stride Duration:</span>
                      <span className="trial-review-metric-value">1.24s ± 0.08</span>
                    </div>
                    <div className="trial-review-metric-row">
                      <span className="trial-review-metric-label">Stance Phase:</span>
                      <span className="trial-review-metric-value">68.5% ± 3.2</span>
                    </div>
                    <div className="trial-review-metric-row">
                      <span className="trial-review-metric-label">Swing Phase:</span>
                      <span className="trial-review-metric-value">31.5% ± 2.8</span>
                    </div>
                    <div className="trial-review-metric-row">
                      <span className="trial-review-metric-label">Double Support:</span>
                      <span className="trial-review-metric-value">12.8% ± 1.5</span>
                    </div>
                  </div>
                </div>
                <div>
                  <h4 style={{fontWeight: '500', color: '#374151', marginBottom: '0.75rem'}}>Spatial Parameters</h4>
                  <div className="trial-review-metrics">
                    <div className="trial-review-metric-row">
                      <span className="trial-review-metric-label">Stride Width:</span>
                      <span className="trial-review-metric-value positive">12.4cm ± 1.8</span>
                    </div>
                    <div className="trial-review-metric-row">
                      <span className="trial-review-metric-label">Step Length Ratio:</span>
                      <span className="trial-review-metric-value neutral">0.94 ± 0.06</span>
                    </div>
                    <div className="trial-review-metric-row">
                      <span className="trial-review-metric-label">Foot Angle:</span>
                      <span className="trial-review-metric-value">8.2° ± 2.1</span>
                    </div>
                    <div className="trial-review-metric-row">
                      <span className="trial-review-metric-label">Base of Support:</span>
                      <span className="trial-review-metric-value accent">11.8cm ± 2.3</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Notes Tab */}
        {activeTab === 'notes' && (
          <div className="trial-review-section">
            <div className="trial-review-card">
              <h3 className="trial-review-card-title">Clinical Assessment Notes</h3>
              <div className="trial-review-notes">
                <div className="trial-review-note-section">
                  <h4>Veterinary Observations</h4>
                  <div className="trial-review-note-content gray">
                    <p className="trial-review-note-text">
                      Subject demonstrates significant improvement in gait symmetry post-surgery. Notable reduction in 
                      compensatory movements. Weight-bearing capacity has increased substantially on affected limb. 
                      No signs of pain or discomfort during assessment.
                    </p>
                  </div>
                </div>
                <div className="trial-review-note-section">
                  <h4>Biomechanical Assessment</h4>
                  <div className="trial-review-note-content gray">
                    <p className="trial-review-note-text">
                      Ground reaction forces show normalized loading patterns. Stride length progression indicates 
                      increasing confidence in locomotion. Joint angles within normal physiological ranges. 
                      Coordination between limbs improving steadily.
                    </p>
                  </div>
                </div>
                <div className="trial-review-note-section">
                  <h4>Treatment Recommendations</h4>
                  <div className="trial-review-note-content blue">
                    <p className="trial-review-note-text blue">
                      Continue current physical therapy protocol. Increase exercise duration gradually. 
                      Schedule follow-up gait analysis in 2 weeks. Consider introducing more complex terrain 
                      for advanced rehabilitation training.
                    </p>
                  </div>
                </div>
                <div className="trial-review-note-section">
                  <h4>Recovery Status</h4>
                  <div className="trial-review-note-content gray">
                    <p className="trial-review-note-text">
                      <strong>Week 6 Post-Surgery:</strong> Excellent progress. Functional mobility restored to 85% of baseline. 
                      Pain management effective. Subject showing enthusiasm for activity. 
                      Prognosis: Full recovery expected within 2-3 additional weeks.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TrialReview;