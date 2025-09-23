import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';

const Dashboard = () => {
  const [showMap, setShowMap] = useState(true);
  const [position, setPosition] = useState([51.505, -0.09]);

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

  return (
    <div className={`dashboard ${!showMap ? 'map-hidden' : ''}`}>
      <div className="chat-container">
        <div className="header">
          <img src="https://img.icons8.com/color/48/000000/chat--v1.png" alt="Chat Logo" />
          <h1>Conversational UI</h1>
        </div>
        <div className="controls">
          <select>
            <option>Select Profession</option>
            <option>Doctor</option>
            <option>Engineer</option>
            <option>Teacher</option>
          </select>
          <select>
            <option>Select Location</option>
            <option>New York</option>
            <option>London</option>
            <option>Tokyo</option>
          </select>
        </div>
        <div className="chat-input">
          <input type="text" placeholder="Type your message..." />
          <button>Send</button>
        </div>
      </div>
      <div className="map-container">
        <button className="map-toggle-button" onClick={() => setShowMap(!showMap)}>
          {showMap ? 'Hide Map' : 'Show Map'}
        </button>
        {showMap && (
          <>
            <MapContainer center={position} zoom={13} scrollWheelZoom={true} key={position.join(',')}>
              <TileLayer
                attribution='&copy; <a href="httpsa://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <Marker position={position}>
                <Popup>
                  Your current location.
                </Popup>
              </Marker>
            </MapContainer>
            <button className="fetch-button">Fetch</button>
          </>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
