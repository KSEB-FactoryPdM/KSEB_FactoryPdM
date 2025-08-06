'use client'
import React from 'react'

export default function EquipmentFilter({ options, value, onChange }: { options: string[]; value: string; onChange: (v: string) => void }) {
  return (
    <select className="border rounded px-2 py-1" value={value} onChange={(e) => onChange(e.target.value)}>
      <option value="">All Equipment</option>
      {options.map((opt) => (
        <option key={opt} value={opt}>
          {opt}
        </option>
      ))}
    </select>
  )
}
