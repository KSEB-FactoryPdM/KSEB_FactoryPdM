'use client'
import Image from 'next/image'
import { AlertItem } from '@/mockData'

export default function AlertDetailsModal({
  alert,
  onClose,
}: {
  alert: AlertItem
  onClose: () => void
}) {
  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-md p-4 w-80"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-lg font-heading mb-2">Alert Details</h3>
        <p className="text-sm mb-1">
          <strong>Time:</strong> {alert.time}
        </p>
        <p className="text-sm mb-1">
          <strong>Device:</strong> {alert.device}
        </p>
        <p className="text-sm mb-1">
          <strong>Type:</strong> {alert.type}
        </p>
        <p className="text-sm mb-1">
          <strong>Severity:</strong> {alert.severity}
        </p>
        <p className="text-sm mb-2">
          <strong>Cause:</strong> {alert.cause}
        </p>
        {alert.snapshot && (
          <Image
            src={alert.snapshot}
            alt="Sensor snapshot"
            width={320}
            height={180}
            className="mb-2"
          />
        )}
        <button
          className="mt-2 px-4 py-1 bg-primary text-white rounded"
          onClick={onClose}
        >
          Close
        </button>
      </div>
    </div>
  )
}
