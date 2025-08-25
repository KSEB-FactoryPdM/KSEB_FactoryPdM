'use client'
import React from 'react'

export type SensorOption = { value: string; label: string }

export default function SensorFilter({
  options,
  value,
  onChange,
}: {
  options: SensorOption[]
  value: string
  onChange: (v: string) => void
}) {
  return (
    <select className="border rounded px-2 py-1" value={value} onChange={(e) => onChange(e.target.value)}>
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  )
}
