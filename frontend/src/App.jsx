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
    <div className="h-screen grid grid-cols-[60%_40%] bg-[linear-gradient(180deg,#0b0518_0%,#120b2a_100%)]">
      <LeftPanel
        profession={profession}
        onChangeProfession={setProfession}
        location={location}
        onChangeLocation={setLocation}
        messages={messages}
        onSend={(text) => appendMessage('user', text)}
      />
      <div className="relative bg-white/90 backdrop-blur supports-[backdrop-filter]:bg-white/80">
        <div className="absolute inset-0 pointer-events-none bg-gradient-to-b from-transparent via-transparent to-purple-50" />
        <MapView
          profession={profession}
          onAppendMessage={(content) => appendMessage('system', content)}
        />
      </div>
    </div>
  )
}


