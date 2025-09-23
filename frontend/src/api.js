import axios from 'axios'

export const api = axios.create({ baseURL: '/api' })

export function postNearestFloat(lat, lon, profession) {
  return api.post('/get_nearest_float', { lat, lon, profession }).then(r => r.data)
}


