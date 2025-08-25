'use client'
import React from 'react'

type Anomaly = { id: string | number; equipmentId: string; type: string; timestamp: string; status?: string; description?: string; severity?: string }

export default function AnomalyDetailsModal({ anomaly, onClose }: { anomaly: Anomaly; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-md p-4 w-[22rem]" onClick={(e) => e.stopPropagation()}>
        <h3 className="text-lg font-heading mb-2">Anomaly Details</h3>
        <div className="space-y-1 text-sm">
          <p><strong>ID:</strong> {anomaly.id}</p>
          <p><strong>Time:</strong> {new Date(anomaly.timestamp).toLocaleString()}</p>
          <p><strong>Equipment:</strong> {anomaly.equipmentId}</p>
          <p><strong>Type:</strong> {anomaly.type}</p>
          <p><strong>Status:</strong> {anomaly.status ?? '-'}</p>
          {anomaly.severity && <p><strong>Severity:</strong> {anomaly.severity}</p>}
          {anomaly.description && (
            <p className="pt-1"><strong>Description:</strong> {anomaly.description}</p>
          )}
        </div>
        <button className="mt-3 px-4 py-1 bg-primary text-white rounded" onClick={onClose}>Close</button>
      </div>
    </div>
  )
}

