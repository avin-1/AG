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
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-[1000]">
        <button
          onClick={fetchNearest}
          disabled={!hasMarker || loading}
          className="rounded-lg bg-indigo-600 px-8 py-4 text-white font-semibold hover:bg-indigo-700 shadow-2xl disabled:bg-gray-500 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105 disabled:scale-100"
        >
          {loading ? 'Fetching...' : 'Fetch Nearest Float'}
        </button>
      </div>
    </div>
  )
}


