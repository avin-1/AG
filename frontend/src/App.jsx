import { useState } from 'react'
import LeftPanel from './components/LeftPanel.jsx'
import MapView from './components/MapView.jsx'

export default function App() {
  const [profession, setProfession] = useState('researcher')
  const [location, setLocation] = useState('')
  const [messages, setMessages] = useState([])

  function appendMessage(role, content) {
    setMessages((prev) => [...prev, { role, content }])
  }

  return (
    <div className="h-screen grid grid-cols-[40%_60%]">
      <LeftPanel
        profession={profession}
        onChangeProfession={setProfession}
        location={location}
        onChangeLocation={setLocation}
        messages={messages}
        onSend={(text) => appendMessage('user', text)}
      />
      <div className="relative">
        <MapView
          profession={profession}
          onAppendMessage={(content) => appendMessage('system', content)}
        />
      </div>
    </div>
  )
}


