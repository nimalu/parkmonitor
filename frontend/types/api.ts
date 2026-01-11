export interface ParkingLot {
  id: string
  name: string
  total: number
  lot_type: string
  latitude: number
  longitude: number
}

export interface CurrentStatus {
  lot_id: string
  name: string
  total: number
  free: number
  occupied: number
  occupancy_rate: number
  timestamp: string
}

export interface Forecast {
  lot_id: string
  name: string
  predicted_occupancy_rate: number
  confidence_low?: number
  confidence_high?: number
  forecast_time: string
}

export interface HealthResponse {
  status: string
  model_loaded: boolean
  model_type?: string
  total_lots: number
}
