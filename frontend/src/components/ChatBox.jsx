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
      <form onSubmit={submit} className="flex items-center gap-2 p-4">
        <input
          className="flex-grow bg-white/5 border border-white/20 rounded-lg px-3 py-2 text-white placeholder-white/70 focus:outline-none focus:ring-2 focus:ring-white/30 backdrop-blur-sm"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button className="rounded-lg bg-gradient-to-r from-[#7c4dff] to-[#536dfe] px-4 py-2 text-white font-semibold hover:opacity-90 shadow-lg">Send</button>
      </form>
    </div>
  )
}


