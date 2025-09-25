import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import AdvancedVisualizations from './AdvancedVisualizations';
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

  // Enhanced visualization component with real ARGO data
  const VisualizationPanel = () => {
    return (
      <div className="visualization-panel">
        <div className="viz-header">
          <h3>🌊 Advanced ARGO Data Analysis</h3>
          <button 
            className="close-viz-btn"
            onClick={() => setShowVisualizations(false)}
          >
            ✕
          </button>
        </div>
        
        <div className="viz-info">
          <p>📍 Select a location on the map to analyze the 2 nearest ARGO floats</p>
          <p>🧠 Get AI-powered comparative analysis and advanced visualizations</p>
        </div>

        <AdvancedVisualizations 
          location={selected || position}
          profession={profession}
        />
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
        {/* Show SQL and nearest platforms if available in last system message meta (we'll append explicitly) */}
        <ChatInput
          onSend={async (text) => {
            if (!text.trim()) return;
            const [lat, lng] = selected || position;
            // Optimistically show user question
            setMessages((prev) => [...prev, { role: 'user', content: text }]);
            try {
              // Call SQL-enhanced endpoint to also get SQL, data, nearest platforms
              const res = await fetch('/api/sql_query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, lat, lon: lng, profession: profession.toLowerCase() }),
              });
              const data = await res.json();
              const sqlBlock = data.sql ? `\n\nSQL Used:\n\n\`\`\`sql\n${data.sql}\n\`\`\`` : '';
              const nearest = Array.isArray(data.nearest_platforms) ? data.nearest_platforms.join(', ') : '';
              const nearestLine = nearest ? `\nNearest Platforms: ${nearest}` : '';
              const tablePreview = Array.isArray(data.data) && data.data.length > 0
                ? `\n\nRows: ${data.data.length} (showing up to 3)\n\n` +
                  '```\n' + JSON.stringify(data.data.slice(0, 3), null, 2) + '\n```'
                : '';
              const content = (data.response || 'No answer.') + nearestLine + sqlBlock + tablePreview;
              setMessages((prev) => [...prev, { role: 'system', content }]);
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
