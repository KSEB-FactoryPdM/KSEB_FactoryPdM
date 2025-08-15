'use client'

import React from 'react'

type GrafanaPanelProps = {
  deviceId: string
  height?: number | string
  refresh?: string
  panelId?: number
  variant?: 'solo' | 'dashboard'
  title?: string
  className?: string
  theme?: 'light' | 'dark'
}

const BASE_URL = process.env.NEXT_PUBLIC_GRAFANA_BASE_URL || 'http://localhost:3001'
const DASHBOARD_UID = 'unity-sensor-data'
const DASHBOARD_SLUG = 'unity-sensor-data'

export default function GrafanaPanel({
  deviceId,
  height = 160,
  refresh = '5s',
  panelId,
  variant = (process.env.NEXT_PUBLIC_GRAFANA_EMBED_VARIANT as 'solo' | 'dashboard') || 'solo',
  title,
  className,
  theme,
}: GrafanaPanelProps) {
  const hProp = typeof height === 'number' ? height : Number.parseInt(height as string, 10) || 160

  const qsBase = `orgId=1&kiosk&refresh=${encodeURIComponent(refresh)}&var-device=${encodeURIComponent(
    deviceId,
  )}${theme ? `&theme=${encodeURIComponent(theme)}` : ''}`

  const useSolo = variant === 'solo' && typeof panelId === 'number' && Number.isFinite(panelId)
  const src = useSolo
    ? `${BASE_URL}/d-solo/${DASHBOARD_UID}/${DASHBOARD_SLUG}?panelId=${encodeURIComponent(
        String(panelId!),
      )}&${qsBase}`
    : `${BASE_URL}/d/${DASHBOARD_UID}/${DASHBOARD_SLUG}?${qsBase}`

  return (
    <div className={className}>
      {title ? (
        <div className="mb-1 text-sm font-medium text-slate-700">{title}</div>
      ) : null}
      <iframe
        src={src}
        title={title || `grafana-${deviceId}-${variant}${panelId ? `-${panelId}` : ''}`}
        width="100%"
        height={hProp}
        frameBorder={0}
        loading="lazy"
        referrerPolicy="no-referrer"
      />
    </div>
  )
}
