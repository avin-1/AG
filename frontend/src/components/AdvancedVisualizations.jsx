import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';

const AdvancedVisualizations = ({ location, profession }) => {
  const [floats, setFloats] = useState([]);
  const [analysis, setAnalysis] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeChart, setActiveChart] = useState('map');

  const fetchNearestFloats = async () => {
    if (!location) return;
    
    setLoading(true);
    try {
      const response = await fetch('/api/get_nearest_floats', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          lat: location[0], 
          lon: location[1], 
          profession: profession.toLowerCase() 
        }),
      });
      const data = await response.json();
      setFloats(data.floats || []);
    } catch (error) {
      console.error('Error fetching floats:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchComparativeAnalysis = async () => {
    if (!location) return;
    
    setLoading(true);
    try {
      const response = await fetch('/api/comparative_analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          lat: location[0], 
          lon: location[1], 
          profession: profession.toLowerCase() 
        }),
      });
      const data = await response.json();
      setFloats(data.floats || []);
      setAnalysis(data.analysis || '');
    } catch (error) {
      console.error('Error fetching analysis:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (location) {
      fetchNearestFloats();
    }
  }, [location]);

  const createMapPlot = () => {
    if (floats.length === 0) return null;

    const floatData = floats.map((float, index) => ({
      x: [float.lon],
      y: [float.lat],
      mode: 'markers',
      type: 'scatter',
      name: `Float ${float.id}`,
      marker: {
        size: 15,
        color: index === 0 ? '#ff6b6b' : '#4ecdc4',
        symbol: index === 0 ? 'star' : 'circle',
        line: { width: 2, color: 'white' }
      },
      text: [
        `Float ${float.id}<br>` +
        `Location: ${float.lat.toFixed(4)}°N, ${float.lon.toFixed(4)}°E<br>` +
        `Temperature: ${float.temperature || 'N/A'}°C<br>` +
        `Salinity: ${float.salinity || 'N/A'} PSU`
      ],
      hovertemplate: '%{text}<extra></extra>'
    }));

    // Add user location
    floatData.push({
      x: [location[1]],
      y: [location[0]],
      mode: 'markers',
      type: 'scatter',
      name: 'Your Location',
      marker: {
        size: 20,
        color: '#7c3aed',
        symbol: 'diamond',
        line: { width: 3, color: 'white' }
      },
      text: ['Your Location'],
      hovertemplate: 'Your Location<br>Lat: %{y:.4f}°N<br>Lon: %{x:.4f}°E<extra></extra>'
    });

    return {
      data: floatData,
      layout: {
        title: {
          text: 'ARGO Float Locations & Your Position',
          font: { color: '#e9ddff', size: 20 }
        },
        xaxis: {
          title: 'Longitude (°E)',
          gridcolor: 'rgba(167,139,250,0.2)',
          color: '#e9ddff'
        },
        yaxis: {
          title: 'Latitude (°N)',
          gridcolor: 'rgba(167,139,250,0.2)',
          color: '#e9ddff'
        },
        plot_bgcolor: 'rgba(0,0,0,0)',
        paper_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#e9ddff' },
        legend: { 
          bgcolor: 'rgba(0,0,0,0.5)',
          bordercolor: 'rgba(167,139,250,0.3)',
          borderwidth: 1
        },
        margin: { t: 60, b: 60, l: 60, r: 60 }
      }
    };
  };

  const createComparisonChart = () => {
    if (floats.length < 2) return null;

    const float1 = floats[0];
    const float2 = floats[1];

    return {
      data: [
        {
          x: ['Temperature (°C)', 'Salinity (PSU)'],
          y: [float1.temperature || 0, float1.salinity || 0],
          type: 'bar',
          name: `Float ${float1.id}`,
          marker: { color: '#ff6b6b' }
        },
        {
          x: ['Temperature (°C)', 'Salinity (PSU)'],
          y: [float2.temperature || 0, float2.salinity || 0],
          type: 'bar',
          name: `Float ${float2.id}`,
          marker: { color: '#4ecdc4' }
        }
      ],
      layout: {
        title: {
          text: 'Comparative Analysis: Temperature & Salinity',
          font: { color: '#e9ddff', size: 20 }
        },
        xaxis: {
          gridcolor: 'rgba(167,139,250,0.2)',
          color: '#e9ddff'
        },
        yaxis: {
          gridcolor: 'rgba(167,139,250,0.2)',
          color: '#e9ddff'
        },
        plot_bgcolor: 'rgba(0,0,0,0)',
        paper_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#e9ddff' },
        legend: { 
          bgcolor: 'rgba(0,0,0,0.5)',
          bordercolor: 'rgba(167,139,250,0.3)',
          borderwidth: 1
        },
        barmode: 'group',
        margin: { t: 60, b: 60, l: 60, r: 60 }
      }
    };
  };

  const createScatterPlot = () => {
    if (floats.length < 2) return null;

    const float1 = floats[0];
    const float2 = floats[1];

    return {
      data: [
        {
          x: [float1.temperature],
          y: [float1.salinity],
          mode: 'markers',
          type: 'scatter',
          name: `Float ${float1.id}`,
          marker: {
            size: 20,
            color: '#ff6b6b',
            symbol: 'star',
            line: { width: 2, color: 'white' }
          },
          text: [`Float ${float1.id}<br>Temp: ${float1.temperature}°C<br>Sal: ${float1.salinity} PSU`],
          hovertemplate: '%{text}<extra></extra>'
        },
        {
          x: [float2.temperature],
          y: [float2.salinity],
          mode: 'markers',
          type: 'scatter',
          name: `Float ${float2.id}`,
          marker: {
            size: 20,
            color: '#4ecdc4',
            symbol: 'circle',
            line: { width: 2, color: 'white' }
          },
          text: [`Float ${float2.id}<br>Temp: ${float2.temperature}°C<br>Sal: ${float2.salinity} PSU`],
          hovertemplate: '%{text}<extra></extra>'
        }
      ],
      layout: {
        title: {
          text: 'Temperature vs Salinity Scatter Plot',
          font: { color: '#e9ddff', size: 20 }
        },
        xaxis: {
          title: 'Temperature (°C)',
          gridcolor: 'rgba(167,139,250,0.2)',
          color: '#e9ddff'
        },
        yaxis: {
          title: 'Salinity (PSU)',
          gridcolor: 'rgba(167,139,250,0.2)',
          color: '#e9ddff'
        },
        plot_bgcolor: 'rgba(0,0,0,0)',
        paper_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#e9ddff' },
        legend: { 
          bgcolor: 'rgba(0,0,0,0.5)',
          bordercolor: 'rgba(167,139,250,0.3)',
          borderwidth: 1
        },
        margin: { t: 60, b: 60, l: 60, r: 60 }
      }
    };
  };

  const renderChart = () => {
    switch (activeChart) {
      case 'map':
        return createMapPlot();
      case 'comparison':
        return createComparisonChart();
      case 'scatter':
        return createScatterPlot();
      default:
        return null;
    }
  };

  return (
    <div className="advanced-visualizations">
      <div className="viz-header">
        <h3>🌊 Advanced ARGO Data Analysis</h3>
        <div className="viz-controls">
          <button 
            className={`viz-btn ${activeChart === 'map' ? 'active' : ''}`}
            onClick={() => setActiveChart('map')}
          >
            🗺️ Map View
          </button>
          <button 
            className={`viz-btn ${activeChart === 'comparison' ? 'active' : ''}`}
            onClick={() => setActiveChart('comparison')}
          >
            📊 Comparison
          </button>
          <button 
            className={`viz-btn ${activeChart === 'scatter' ? 'active' : ''}`}
            onClick={() => setActiveChart('scatter')}
          >
            📈 Scatter Plot
          </button>
          <button 
            className="analysis-btn"
            onClick={fetchComparativeAnalysis}
            disabled={loading}
          >
            {loading ? 'Analyzing...' : '🧠 AI Analysis'}
          </button>
        </div>
      </div>

      {loading && (
        <div className="loading-indicator">
          <div className="loading-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <span>Loading ARGO data...</span>
        </div>
      )}

      {floats.length > 0 && (
        <div className="viz-content">
          <div className="chart-container">
            {renderChart() && (
              <Plot
                data={renderChart().data}
                layout={renderChart().layout}
                style={{ width: '100%', height: '500px' }}
                config={{
                  displayModeBar: true,
                  displaylogo: false,
                  modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
                }}
              />
            )}
          </div>

          {analysis && (
            <div className="analysis-section">
              <h4>🤖 AI Comparative Analysis</h4>
              <div className="analysis-content">
                <pre style={{ 
                  whiteSpace: 'pre-wrap', 
                  fontFamily: 'inherit',
                  color: '#e9ddff',
                  lineHeight: '1.6',
                  background: 'rgba(255,255,255,0.05)',
                  padding: '20px',
                  borderRadius: '12px',
                  border: '1px solid rgba(167,139,250,0.2)'
                }}>
                  {analysis}
                </pre>
              </div>
            </div>
          )}

          <div className="float-details">
            <h4>📊 Float Details</h4>
            <div className="float-cards">
              {floats.map((float, index) => (
                <div key={float.id} className={`float-card ${index === 0 ? 'primary' : 'secondary'}`}>
                  <div className="float-header">
                    <h5>Float {float.id}</h5>
                    <span className="float-rank">
                      {index === 0 ? '🥇 Closest' : '🥈 Second'}
                    </span>
                  </div>
                  <div className="float-data">
                    <div className="data-item">
                      <span className="label">Location:</span>
                      <span className="value">{float.lat.toFixed(4)}°N, {float.lon.toFixed(4)}°E</span>
                    </div>
                    <div className="data-item">
                      <span className="label">Temperature:</span>
                      <span className="value">{float.temperature || 'N/A'}°C</span>
                    </div>
                    <div className="data-item">
                      <span className="label">Salinity:</span>
                      <span className="value">{float.salinity || 'N/A'} PSU</span>
                    </div>
                    <div className="data-item">
                      <span className="label">Depth Range:</span>
                      <span className="value">
                        {float.depth_min || 'N/A'} - {float.depth_max || 'N/A'} m
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {floats.length === 0 && !loading && (
        <div className="no-data-message">
          <h4>📍 No Data Available</h4>
          <p>Select a location on the map to see ARGO float analysis and visualizations.</p>
        </div>
      )}
    </div>
  );
};

export default AdvancedVisualizations;
