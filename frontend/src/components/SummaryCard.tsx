'use client'
import React from 'react'

export default function SummaryCard({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="bg-white rounded-lg shadow-md p-4 h-20 flex flex-col items-center justify-center">
      <span className="text-sm text-text-primary">{label}</span>
      <span className="text-2xl font-bold">{value}</span>
    </div>
  )
}
