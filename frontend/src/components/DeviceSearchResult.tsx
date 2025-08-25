'use client'

import DeviceSensorPanel from './DeviceSensorPanel'
import type { AlertItem } from '@/mockData'

interface Device {
  id: string
  name: string
  type: string
  status: string
}

interface Props {
  device: Device
  alerts: AlertItem[]
}

export default function DeviceSearchResult({ device, alerts }: Props) {
  return (
    <div className="bg-white rounded-lg shadow p-4 md:flex md:gap-4">
      <div className="md:w-1/2">
        <DeviceSensorPanel deviceId={device.id} sensor="current" height={200} />
      </div>
      <div className="md:w-1/2 mt-4 md:mt-0 space-y-2">
        <h3 className="text-lg font-semibold">{device.name}</h3>
        <p className="text-sm text-neutral-600">ID: {device.id}</p>
        <p className="text-sm text-neutral-600">Type: {device.type}</p>
        <p className="text-sm text-neutral-600">Status: {device.status}</p>
        <h4 className="font-medium mt-2">Alerts</h4>
        {alerts.length === 0 ? (
          <p className="text-sm text-neutral-500">No alerts</p>
        ) : (
          <ul className="list-disc list-inside text-sm">
            {alerts.map((a) => (
              <li key={a.id}>
                <span className="font-medium">{a.type}</span> - {a.severity}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

