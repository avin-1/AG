const options = [
  { value: 'researcher', label: 'Researcher' },
  { value: 'fisherman', label: 'Fisherman' },
  { value: 'policymaker', label: 'Policymaker' },
  { value: 'student', label: 'Student' },
]

export default function ProfessionSelector({ value, onChange }) {
  return (
    <div className="flex items-center gap-3">
      <label className="text-sm font-medium text-gray-700">Profession</label>
      <select
        className="border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  )
}


