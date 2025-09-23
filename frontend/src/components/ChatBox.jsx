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
      <form onSubmit={submit} className="flex items-center gap-3">
        <input
          className="flex-grow bg-[#3c2a58] border border-transparent rounded-lg px-4 py-3 text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-[#5b457a]"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button className="rounded-lg bg-[#5b457a] px-5 py-3 text-white font-semibold hover:bg-opacity-90 shadow-lg transition-colors">Send</button>
      </form>
    </div>
  )
}


