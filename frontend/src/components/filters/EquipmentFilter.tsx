'use client'
import React from 'react'
import { useTranslation } from 'react-i18next'

export interface Machine {
  power: string
  id: string
  statuses: string[]
}

interface Props {
  machines: Machine[]
  power: string
  device: string
  onPowerChange: (v: string) => void
  onDeviceChange: (v: string) => void
}

export default function EquipmentFilter({ machines, power, device, onPowerChange, onDeviceChange }: Props) {
  const { t } = useTranslation('common')
  const powerOptions = Array.from(new Set(machines.map((m) => m.power))).sort()
  const deviceOptions = Array.from(
    new Set(
      machines
        .filter((m) => !power || m.power === power)
        .map((m) => m.id),
    ),
  ).sort()

  return (
    <div className="flex gap-2">
      <select
        className="border rounded px-2 py-1"
        value={power}
        onChange={(e) => {
          onPowerChange(e.target.value)
          onDeviceChange('')
        }}
        aria-label={t('filters.power')}
      >
        <option value="">{t('filters.allPower')}</option>
        {powerOptions.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
      <select
        className="border rounded px-2 py-1"
        value={device}
        onChange={(e) => onDeviceChange(e.target.value)}
        aria-label={t('filters.equipment')}
      >
        <option value="">{t('filters.allEquipment')}</option>
        {deviceOptions.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    </div>
  )
}
