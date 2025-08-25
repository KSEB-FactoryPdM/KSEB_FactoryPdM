export const anomalyLog = [
  { id: 1, time: '2024-05-01 10:00', description: 'High vibration detected', severity: 'High' },
  { id: 2, time: '2024-05-02 11:15', description: 'Temperature spike', severity: 'Medium' },
  { id: 3, time: '2024-05-03 09:30', description: 'Unusual noise', severity: 'Low' },
]

export const summaryReports = [
  { label: 'Downtime (h)', value: 5 },
  { label: 'Alarms', value: 12 },
  { label: 'Repairs', value: 3 },
]

export const distributionData = [
  { bin: '0-10', count: 4 },
  { bin: '10-20', count: 7 },
  { bin: '20-30', count: 3 },
  { bin: '30-40', count: 6 },
  { bin: '40-50', count: 2 },
]

export const heatmapData = [
  { x: 1, y: 1, value: 5 },
  { x: 1, y: 2, value: 8 },
  { x: 1, y: 3, value: 2 },
  { x: 2, y: 1, value: 7 },
  { x: 2, y: 2, value: 3 },
  { x: 2, y: 3, value: 6 },
  { x: 3, y: 1, value: 4 },
  { x: 3, y: 2, value: 1 },
  { x: 3, y: 3, value: 9 },
]

export interface AlertItem {
  id: number
  time: string
  power: string
  device: string
  type: string
  severity: string
  status?: string
  cause: string
  snapshot: string
}

export const alertList: AlertItem[] = [
  {
    id: 1002,
    time: '2025-08-19 02:20',
    power: '2.2kW',
    device: 'L-DEF-01',
    type: 'Current',
    severity: 'Critical',
    status: 'new',
    cause: 'Current threshold exceeded',
    snapshot: '/globe.svg',
  },
  {
    id: 1001,
    time: '2025-08-19 02:21',
    power: '2.2kW',
    device: 'L-DEF-01',
    type: 'Vibration',
    severity: 'Critical',
    status: 'new',
    cause: 'Vibration anomaly detected',
    snapshot: '/globe.svg',
  },
]
