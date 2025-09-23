import { useState } from 'react';
import LeftPanel from './components/LeftPanel.jsx';
import MapView from './components/MapView.jsx';
import { FaChevronLeft, FaChevronRight } from 'react-icons/fa';

export default function App() {
  const [profession, setProfession] = useState('researcher');
  const [location, setLocation] = useState('');
  const [messages, setMessages] = useState([]);
  const [isMapVisible, setIsMapVisible] = useState(true);

  function appendMessage(role, content) {
    setMessages((prev) => [...prev, { role, content }]);
  }

  return (
    <div
      className={`h-screen grid transition-all duration-300 ease-in-out ${
        isMapVisible ? 'grid-cols-[40%_60%]' : 'grid-cols-[100%_0%]'
      }`}
    >
      <LeftPanel
        profession={profession}
        onChangeProfession={setProfession}
        location={location}
        onChangeLocation={setLocation}
        messages={messages}
        onSend={(text) => appendMessage('user', text)}
      />
      <div className="relative">
        <button
          onClick={() => setIsMapVisible(!isMapVisible)}
          className="absolute top-1/2 -left-4 z-10 bg-gray-800 text-white p-2 rounded-full transform -translate-y-1/2 focus:outline-none"
          aria-label={isMapVisible ? 'Collapse map' : 'Expand map'}
        >
          {isMapVisible ? <FaChevronLeft /> : <FaChevronRight />}
        </button>
        <MapView
          profession={profession}
          onAppendMessage={(content) => appendMessage('system', content)}
        />
      </div>
    </div>
  );
}


