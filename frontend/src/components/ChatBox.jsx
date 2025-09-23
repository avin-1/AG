import { useState } from 'react'

export default function ChatBox({ messages = [], onSend }) {
  const [input, setInput] = useState('')

  function submit(e) {
    e.preventDefault()
    if (!input.trim()) return
    onSend?.(input)
    setInput('')
  }

  return (
    <div className="flex flex-col">
      <div className="flex-1 overflow-auto space-y-2 pr-1 mb-3 max-h-[55vh]">
        {messages.map((m, idx) => (
          <div key={idx} className={m.role === 'user' ? 'text-right' : 'text-left'}>
            <span className={`inline-block px-3 py-2 rounded-lg text-sm ${m.role === 'user' ? 'bg-purple-500/30' : 'bg-white/10'} text-white border border-white/10 backdrop-blur-sm`}>{m.content}</span>
          </div>
        ))}
      </div>
      <form onSubmit={submit} className="flex items-center gap-4">
        <input
          className="flex-grow bg-gray-800 border border-gray-700 rounded-lg px-4 py-4 text-white text-lg placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all duration-300 hover:border-indigo-500"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button className="rounded-lg bg-indigo-600 px-6 py-4 text-white font-semibold hover:bg-indigo-700 shadow-lg transition-all duration-300 transform hover:scale-105">Send</button>
      </form>
    </div>
  )
}


