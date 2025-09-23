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
    <div className="h-full bg-gradient-to-b from-[#2d1b4c] to-[#1b0f2c] text-white p-6 flex flex-col">
      <div className="text-2xl font-semibold mb-6 flex items-center gap-3">
        <div className="w-10 h-10 flex items-center justify-center bg-white/10 rounded-lg">
          <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18.068l-3.53-3.53a2.5 2.5 0 113.53-3.53l3.53 3.53a2.5 2.5 0 01-3.53 3.53z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.929 4.929a10 10 0 1114.142 14.142A10 10 0 014.929 4.929z" />
          </svg>
        </div>
        <span>FloatChat</span>
      </div>

      <div className="flex flex-col gap-4 mb-6">
        <div className="relative">
          <select
            className="appearance-none w-full bg-[#3c2a58] border border-transparent rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-[#5b457a]"
            value={profession}
            onChange={(e) => onChangeProfession(e.target.value)}
          >
            <option value="researcher">Select Profession</option>
            <option value="researcher">Researcher</option>
            <option value="fisherman">Fisherman</option>
            <option value="policymaker">Policymaker</option>
            <option value="student">Student</option>
          </select>
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-white">
            <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" /></svg>
          </div>
        </div>

        <div className="relative">
          <select
            className="appearance-none w-full bg-[#3c2a58] border border-transparent rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-[#5b457a]"
            value={location}
            onChange={(e) => onChangeLocation(e.target.value)}
          >
            <option value="">Select Location</option>
            <option value="pune">Pune</option>
            <option value="mumbai">Mumbai</option>
          </select>
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-white">
            <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" /></svg>
          </div>
        </div>
      </div>

      <div className="flex-grow flex flex-col justify-end">
        <ChatBox messages={messages} onSend={onSend} />
      </div>
    </div>
  )
}


