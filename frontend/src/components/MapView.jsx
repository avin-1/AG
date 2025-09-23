import { useState } from 'react'
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { postNearestFloat } from '../api'

function ClickableMarker({ onSet }) {
  useMapEvents({
    click(e) {
      onSet([e.latlng.lat, e.latlng.lng])
    },
  })
  return null
}

export default function MapView({ profession, onAppendMessage }) {
  const [position, setPosition] = useState([18.5204, 73.8567]) // Pune
  const [hasMarker, setHasMarker] = useState(false)
  const [loading, setLoading] = useState(false)

  async function fetchNearest() {
    if (!hasMarker) return
    setLoading(true)
    try {
      const [lat, lon] = position
      const data = await postNearestFloat(lat, lon, profession)
      onAppendMessage?.(JSON.stringify(data))
    } catch (e) {
      onAppendMessage?.('Failed to fetch nearest float')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1">
        <MapContainer center={position} zoom={11} className="h-full">
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          <ClickableMarker onSet={(pos) => { setPosition(pos); setHasMarker(true); }} />
          {hasMarker && <Marker position={position} />}
        </MapContainer>
      </div>
      <div className="p-3 border-t flex items-center justify-end bg-white">
        <button onClick={fetchNearest} disabled={!hasMarker || loading} className="rounded-lg bg-gradient-to-r from-[#7c4dff] to-[#536dfe] px-4 py-2 text-white font-semibold hover:opacity-90 shadow">
          {loading ? 'Fetching...' : 'Fetch'}
        </button>
      </div>
    </div>
  )
}


