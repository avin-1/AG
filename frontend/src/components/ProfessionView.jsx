function FishermanView({ data }) {
  if (!data) return <Empty />
  const t = data?.temperature ?? '—'
  const s = data?.salinity ?? '—'
  return <div className="text-sm">Safe fishing conditions. Expected temperature {t}°C, salinity {s} PSU.</div>
}

function ResearcherView({ data }) {
  if (!data) return <Empty />
  return (
    <div className="space-y-2">
      <div className="text-sm text-gray-700">Float ID: {data.id || '—'}</div>
      <div className="text-sm text-gray-700">Location: {data.lat?.toFixed?.(3)}, {data.lon?.toFixed?.(3)}</div>
      <div className="text-sm text-gray-700">Latest profile depth range: {data.depth_min ?? '—'}–{data.depth_max ?? '—'} m</div>
      <div className="text-xs text-gray-500">Charts placeholder: depth vs temperature, salinity trends</div>
    </div>
  )
}

function PolicymakerView({ data }) {
  if (!data) return <Empty />
  return <div className="text-sm">In this region, salinity has been stable; suitable for fisheries policy decisions.</div>
}

function StudentView({ data }) {
  if (!data) return <Empty />
  return (
    <div className="space-y-2 text-sm">
      <div>Nearby ARGO float found with temperature {data.temperature ?? '—'}°C and salinity {data.salinity ?? '—'} PSU.</div>
      <div className="text-gray-600">Glossary: Salinity = amount of salt in water; Temperature = how hot/cold water is.</div>
    </div>
  )
}

function Empty() {
  return <div className="text-sm text-gray-500">No float selected yet.</div>
}

export default function ProfessionView({ profession, data }) {
  const views = {
    fisherman: FishermanView,
    researcher: ResearcherView,
    policymaker: PolicymakerView,
    student: StudentView,
  }
  const View = views[profession] || Empty
  return (
    <div>
      <div className="font-medium mb-2">Result</div>
      <View data={data} />
    </div>
  )
}


