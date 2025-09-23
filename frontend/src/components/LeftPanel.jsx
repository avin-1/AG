import ProfessionSelector from './ProfessionSelector.jsx'
import ChatBox from './ChatBox.jsx'

export default function LeftPanel({
  profession,
  onChangeProfession,
  location,
  onChangeLocation,
  messages,
  onSend,
}) {
  return (
    <div className="h-full bg-gradient-to-br from-[#4b0082] via-[#5b2a86] to-[#7b1fa2] text-white p-6 flex flex-col">
      <div className="text-2xl font-semibold mb-6 flex items-center gap-2">
        <span className="inline-block w-8 h-8 bg-white/20 rounded-md" />
        <span>FloatChat</span>
      </div>

      <div className="flex gap-4 mb-6">
        <select
          className="rounded-lg px-3 py-2 w-1/2 bg-white/5 border border-white/20 text-white placeholder-white/70 focus:outline-none focus:ring-2 focus:ring-white/30 backdrop-blur-sm"
          value={profession}
          onChange={(e) => onChangeProfession(e.target.value)}
        >
          <option className="text-black" value="researcher">Select Profession</option>
          <option className="text-black" value="researcher">Researcher</option>
          <option className="text-black" value="fisherman">Fisherman</option>
          <option className="text-black" value="policymaker">Policymaker</option>
          <option className="text-black" value="student">Student</option>
        </select>

        <select
          className="rounded-lg px-3 py-2 w-1/2 bg-white/5 border border-white/20 text-white placeholder-white/70 focus:outline-none focus:ring-2 focus:ring-white/30 backdrop-blur-sm"
          value={location}
          onChange={(e) => onChangeLocation(e.target.value)}
        >
          <option className="text-black" value="">Select Location</option>
          <option className="text-black" value="pune">Pune</option>
          <option className="text-black" value="mumbai">Mumbai</option>
        </select>
      </div>

      <div className="mt-auto">
        <ChatBox messages={messages} onSend={onSend} />
      </div>
    </div>
  )
}


