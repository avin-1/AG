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
    <div className="h-full flex flex-col relative">
      <div className="flex-1">
        <MapContainer center={position} zoom={11} className="h-full" zoomControl={false}>
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          <ClickableMarker onSet={(pos) => { setPosition(pos); setHasMarker(true); }} />
          {hasMarker && <Marker position={position} />}
        </MapContainer>
      </div>
      <div className="absolute bottom-4 right-4">
        <button onClick={fetchNearest} disabled={!hasMarker || loading} className="rounded-lg bg-[#6a4c9c] px-6 py-3 text-white font-semibold hover:bg-opacity-90 shadow-lg disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors">
          {loading ? 'Fetching...' : 'Fetch'}
        </button>
      </div>
    </div>
  )
}


