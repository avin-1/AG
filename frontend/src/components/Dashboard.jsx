import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

function ChatInput({ onSend }) {
  const [value, setValue] = useState('');
  return (
    <div className="chat-input">
      <input
        type="text"
        placeholder="Ask about this location..."
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => { if (e.key === 'Enter') { onSend?.(value); setValue(''); } }}
      />
      <button onClick={() => { onSend?.(value); setValue(''); }}>Send</button>
    </div>
  );
}

const Dashboard = () => {
  const [showMap, setShowMap] = useState(true);
  const [position, setPosition] = useState([51.505, -0.09]);
  const [selected, setSelected] = useState(null); // [lat, lng]
  const [profession, setProfession] = useState('Researcher');
  const [messages, setMessages] = useState([]); // {role, content}
  const [showVisualizations, setShowVisualizations] = useState(false);
  const [data, setData] = useState(null);
  const [chatWidth, setChatWidth] = useState(50); // Percentage width for chat container
  const [isResizing, setIsResizing] = useState(false);

  useEffect(() => {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setPosition([pos.coords.latitude, pos.coords.longitude]);
      },
      () => {
        // Could handle error here, e.g. show a notification
        console.log("Could not get user location.");
      }
    );
  }, []);

  async function analyzeAt(lat, lng) {
    try {
      const res = await fetch('/api/analyze_location', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lat, lon: lng, profession: profession.toLowerCase() }),
      });
      const data = await res.json();
      const n = data.nearest || {};
      const nearestText = `Nearest Float\nID: ${n.id ?? 'N/A'}\nLat: ${n.lat?.toFixed?.(5)}\nLon: ${n.lon?.toFixed?.(5)}\nTemp: ${n.temperature ?? 'N/A'}\nSalinity: ${n.salinity ?? 'N/A'}`;
      const insights = data.insights || 'No insights available.';
      setMessages((prev) => [
        ...prev,
        { role: 'system', content: insights },
        { role: 'system', content: nearestText },
      ]);
    } catch (e) {
      setMessages((prev) => [...prev, { role: 'system', content: 'Failed to analyze location.' }]);
    }
  }

  function ClickCapture({ onSelect }) {
    useMapEvents({
      click(e) {
        const { lat, lng } = e.latlng;
        onSelect([lat, lng]);
      },
    });
    return null;
  }

  function formatCoord(value) {
    return value.toFixed(5);
  }

  // Resize functionality
  const handleMouseDown = (e) => {
    setIsResizing(true);
    e.preventDefault();
  };

  const handleMouseMove = (e) => {
    if (!isResizing) return;
    
    const containerWidth = window.innerWidth - 48; // Account for padding
    const newChatWidth = (e.clientX / containerWidth) * 100;
    
    // Constrain between 20% and 80%
    const constrainedWidth = Math.min(Math.max(newChatWidth, 20), 80);
    setChatWidth(constrainedWidth);
  };

  const handleMouseUp = () => {
    setIsResizing(false);
  };

  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    } else {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing]);

  // Simple visualization component
  const VisualizationPanel = () => {
    const [chartType, setChartType] = useState('map');
    
    const loadSampleData = () => {
      const sampleData = {
        floats: [
          { id: '1900022', lat: 10.5, lon: 75.2, temp: 28.5, salinity: 35.2 },
          { id: '1900033', lat: 12.1, lon: 78.3, temp: 27.8, salinity: 34.9 },
          { id: '1900034', lat: 8.7, lon: 72.1, temp: 29.1, salinity: 35.5 }
        ]
      };
      setData(sampleData);
    };

    return (
      <div className="visualization-panel">
        <div className="viz-header">
          <h3>📊 ARGO Data Visualizations</h3>
          <button 
            className="close-viz-btn"
            onClick={() => setShowVisualizations(false)}
          >
            ✕
          </button>
        </div>
        
        <div className="viz-controls">
          <button 
            className={`viz-btn ${chartType === 'map' ? 'active' : ''}`}
            onClick={() => setChartType('map')}
          >
            🗺️ Map View
          </button>
          <button 
            className={`viz-btn ${chartType === 'profile' ? 'active' : ''}`}
            onClick={() => setChartType('profile')}
          >
            📈 Profiles
          </button>
          <button 
            className={`viz-btn ${chartType === 'comparison' ? 'active' : ''}`}
            onClick={() => setChartType('comparison')}
          >
            🔬 Comparison
          </button>
        </div>

        {!data && (
          <div className="load-data-section">
            <p>Load ARGO data to see visualizations</p>
            <button className="load-data-btn" onClick={loadSampleData}>
              Load Sample Data
            </button>
          </div>
        )}

        {data && (
          <div className="viz-content">
            {chartType === 'map' && (
              <div className="map-viz">
                <h4>ARGO Float Locations</h4>
                <div className="float-list">
                  {data.floats.map((float, i) => (
                    <div key={i} className="float-item">
                      <strong>Float {float.id}</strong>
                      <div>Lat: {float.lat}°, Lon: {float.lon}°</div>
                      <div>Temp: {float.temp}°C, Salinity: {float.salinity} PSU</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {chartType === 'profile' && (
              <div className="profile-viz">
                <h4>Temperature & Salinity Profiles</h4>
                <div className="profile-data">
                  {data.floats.map((float, i) => (
                    <div key={i} className="profile-item">
                      <h5>Float {float.id}</h5>
                      <div className="profile-bars">
                        <div className="bar">
                          <span>Temperature: {float.temp}°C</span>
                          <div className="bar-fill" style={{width: `${(float.temp/30)*100}%`}}></div>
                        </div>
                        <div className="bar">
                          <span>Salinity: {float.salinity} PSU</span>
                          <div className="bar-fill" style={{width: `${((float.salinity-34)/2)*100}%`}}></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {chartType === 'comparison' && (
              <div className="comparison-viz">
                <h4>Float Comparison</h4>
                <div className="comparison-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Float ID</th>
                        <th>Temperature (°C)</th>
                        <th>Salinity (PSU)</th>
                        <th>Location</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.floats.map((float, i) => (
                        <tr key={i}>
                          <td>{float.id}</td>
                          <td>{float.temp}</td>
                          <td>{float.salinity}</td>
                          <td>{float.lat}°, {float.lon}°</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={`dashboard ${!showMap ? 'map-hidden' : ''} ${showVisualizations ? 'viz-visible' : ''} ${isResizing ? 'resizing' : ''}`}>
      {showVisualizations && <VisualizationPanel />}
      <div 
        className="chat-container"
        style={{ width: `${chatWidth}%` }}
      >
        <div className="header">
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <img src="https://img.icons8.com/color/48/000000/chat--v1.png" alt="Chat Logo" />
            <h1>FloatChat</h1>
          </div>
          <div className="header-buttons">
            <button
              className="viz-toggle-button"
              onClick={() => setShowVisualizations(!showVisualizations)}
              aria-label={showVisualizations ? 'Hide visualizations' : 'Show visualizations'}
            >
              {showVisualizations ? 'Hide Charts' : '📊 Charts'}
            </button>
            <button
              className="map-toggle-button"
              onClick={() => setShowMap(!showMap)}
              aria-label={showMap ? 'Hide map' : 'Show map'}
            >
              {showMap ? 'Hide Map' : 'Show Map'}
            </button>
          </div>
        </div>
        <div className="controls">
          <select value={profession} onChange={(e) => setProfession(e.target.value)}>
            <option>Researcher</option>
            <option>Fisherman</option>
            <option>Policymaker</option>
            <option>Student</option>
          </select>
          <select>
            <option>Select Location</option>
            <option>New York</option>
            <option>London</option>
            <option>Tokyo</option>
          </select>
        </div>
        <div className="messages">
          {messages.map((m, i) => (
            <div key={i} className={`message ${m.role}`}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
            </div>
          ))}
        </div>
        <ChatInput
          onSend={async (text) => {
            if (!text.trim()) return;
            const [lat, lng] = selected || position;
            // Optimistically show user question
            setMessages((prev) => [...prev, { role: 'user', content: text }]);
            try {
              const res = await fetch('/api/ask_with_context', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, lat, lon: lng, profession: profession.toLowerCase() }),
              });
              const data = await res.json();
              setMessages((prev) => [...prev, { role: 'system', content: data.response || 'No answer.' }]);
            } catch (e) {
              setMessages((prev) => [...prev, { role: 'system', content: 'Failed to get answer.' }]);
            }
          }}
        />
      </div>
      
      {/* Resize Handle */}
      {showMap && (
        <div 
          className="resize-handle"
          onMouseDown={handleMouseDown}
        >
          <div className="resize-handle-line"></div>
        </div>
      )}
      
      <div 
        className="map-container"
        style={{ width: `${100 - chatWidth}%` }}
      >
        <div className="map-topbar">
          {selected ? (
            <div className="coords"><span>Lat:</span> {formatCoord(selected[0])} <span>Lng:</span> {formatCoord(selected[1])}</div>
          ) : (
            <div className="coords dims">Click on the map to select coordinates</div>
          )}
        </div>
        {/* Keep bottom Fetch and remove duplicate toggle here since it moved to header */}
        {showMap && (
          <>
            <MapContainer center={position} zoom={13} scrollWheelZoom={true} key={position.join(',')}>
              <TileLayer
                attribution='&copy; <a href="httpsa://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <ClickCapture onSelect={setSelected} />
              <Marker position={selected || position}>
                <Popup>
                  {selected ? 'Selected location' : 'Your current location.'}
                </Popup>
              </Marker>
            </MapContainer>
            <button
              className="fetch-button"
              onClick={() => {
                const [lat, lng] = selected || position;
                analyzeAt(lat, lng);
              }}
            >
              Fetch Insights
            </button>
          </>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
