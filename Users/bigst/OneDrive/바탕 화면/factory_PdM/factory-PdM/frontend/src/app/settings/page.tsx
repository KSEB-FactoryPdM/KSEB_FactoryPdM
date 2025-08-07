'use client'

import { useEffect, useState } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import ChartCard from '@/components/ChartCard'
import ThemeToggle from '@/components/ThemeToggle'
import HighContrastToggle from '@/components/HighContrastToggle'
import FontSizeSelector from '@/components/FontSizeSelector'
import pkg from '../../../package.json'

export default function SettingsPage() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [socketUrl, setSocketUrl] = useState('')
  const [notifications, setNotifications] = useState({
    email: false,
    sms: false,
    push: false,
  })
  const [language, setLanguage] = useState<'en' | 'ko'>('en')
  const [users, setUsers] = useState<{ name: string; role: string }[]>([])
  const [newUserName, setNewUserName] = useState('')
  const [newUserRole, setNewUserRole] = useState('viewer')
  const [modelVersion, setModelVersion] = useState('v1')
  const [detectionThreshold, setDetectionThreshold] = useState(0.5)
  const [plcEndpoint, setPlcEndpoint] = useState('')
  const [mqttEndpoint, setMqttEndpoint] = useState('')
  const [opcuaEndpoint, setOpcuaEndpoint] = useState('')

  useEffect(() => {
    setSocketUrl(
      localStorage.getItem('socketUrl') ||
        process.env.NEXT_PUBLIC_WEBSOCKET_URL ||
        ''
    )
    const storedLang = localStorage.getItem('language') as 'en' | 'ko' | null
    if (storedLang) {
      setLanguage(storedLang)
      if (typeof document !== 'undefined') {
        document.documentElement.lang = storedLang
      }
    }

    const storedUsers = localStorage.getItem('users')
    if (storedUsers) {
      try {
        setUsers(JSON.parse(storedUsers))
      } catch {}
    }
    const mv = localStorage.getItem('modelVersion')
    if (mv) setModelVersion(mv)
    const dt = localStorage.getItem('detectionThreshold')
    if (dt) setDetectionThreshold(parseFloat(dt))
    setPlcEndpoint(localStorage.getItem('plcEndpoint') || '')
    setMqttEndpoint(localStorage.getItem('mqttEndpoint') || '')
    setOpcuaEndpoint(localStorage.getItem('opcuaEndpoint') || '')
  }, [])

  const saveSettings = () => {
    localStorage.setItem('socketUrl', socketUrl)
    localStorage.setItem('language', language)
    localStorage.setItem('profile', JSON.stringify({ name, email }))
    localStorage.setItem('notifications', JSON.stringify(notifications))
    localStorage.setItem('users', JSON.stringify(users))
    localStorage.setItem('modelVersion', modelVersion)
    localStorage.setItem('detectionThreshold', detectionThreshold.toString())
    localStorage.setItem('plcEndpoint', plcEndpoint)
    localStorage.setItem('mqttEndpoint', mqttEndpoint)
    localStorage.setItem('opcuaEndpoint', opcuaEndpoint)
    if (typeof document !== 'undefined') {
      document.documentElement.lang = language
    }
    alert('Settings saved')
  }

  return (
    <DashboardLayout>
      <div className="space-y-4">
        <ChartCard title="System Information">
          <p className="text-sm">Version {pkg.version}</p>
        </ChartCard>
        <ChartCard title="User Profile">
          <div className="space-y-2">
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Name"
              className="w-full bg-input-bg rounded-md p-2 text-sm text-black placeholder:text-text-primary"
            />
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Email"
              className="w-full bg-input-bg rounded-md p-2 text-sm text-black placeholder:text-text-primary"
            />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              className="w-full bg-input-bg rounded-md p-2 text-sm text-black placeholder:text-text-primary"
            />
          </div>
        </ChartCard>

        <ChartCard title="User Management">
          <div className="space-y-2">
            {users.map((u, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <span className="flex-1 text-sm">{u.name} - {u.role}</span>
                <button
                  type="button"
                  className="text-red-600 text-xs"
                  onClick={() => setUsers(users.filter((_, i) => i !== idx))}
                >
                  Remove
                </button>
              </div>
            ))}
            <div className="flex gap-2">
              <input
                value={newUserName}
                onChange={(e) => setNewUserName(e.target.value)}
                placeholder="Name"
                className="flex-1 bg-input-bg rounded-md p-2 text-sm text-black placeholder:text-text-primary"
              />
              <select
                value={newUserRole}
                onChange={(e) => setNewUserRole(e.target.value)}
                className="bg-input-bg rounded-md p-2 text-sm text-black"
              >
                <option value="admin">Admin</option>
                <option value="operator">Operator</option>
                <option value="viewer">Viewer</option>
              </select>
              <button
                type="button"
                onClick={() => {
                  if (!newUserName.trim()) return
                  setUsers([...users, { name: newUserName.trim(), role: newUserRole }])
                  setNewUserName('')
                  setNewUserRole('viewer')
                }}
                className="px-2 py-1 bg-primary text-white rounded"
              >
                Add
              </button>
            </div>
          </div>
        </ChartCard>

        <ChartCard title="Algorithm Configuration">
          <div className="space-y-2">
            <label className="block text-sm">Model Version</label>
            <select
              value={modelVersion}
              onChange={(e) => setModelVersion(e.target.value)}
              className="w-full bg-input-bg rounded-md p-2 text-sm text-black"
            >
              <option value="v1">v1</option>
              <option value="v2">v2</option>
              <option value="v3">v3</option>
            </select>
            <label className="block text-sm">Detection Threshold</label>
            <input
              type="number"
              min="0"
              max="1"
              step="0.01"
              value={detectionThreshold}
              onChange={(e) => setDetectionThreshold(parseFloat(e.target.value))}
              className="w-full bg-input-bg rounded-md p-2 text-sm text-black"
            />
          </div>
        </ChartCard>

        <ChartCard title="Communication Settings">
          <div className="space-y-2">
            <input
              value={plcEndpoint}
              onChange={(e) => setPlcEndpoint(e.target.value)}
              placeholder="PLC/SCADA Endpoint"
              className="w-full bg-input-bg rounded-md p-2 text-sm text-black placeholder:text-text-primary"
            />
            <input
              value={mqttEndpoint}
              onChange={(e) => setMqttEndpoint(e.target.value)}
              placeholder="MQTT Endpoint"
              className="w-full bg-input-bg rounded-md p-2 text-sm text-black placeholder:text-text-primary"
            />
            <input
              value={opcuaEndpoint}
              onChange={(e) => setOpcuaEndpoint(e.target.value)}
              placeholder="OPC UA Endpoint"
              className="w-full bg-input-bg rounded-md p-2 text-sm text-black placeholder:text-text-primary"
            />
          </div>
        </ChartCard>

        <ChartCard title="Connection">
          <div className="space-y-2">
            <label className="block text-sm">NEXT_PUBLIC_WEBSOCKET_URL</label>
            <input
              value={socketUrl}
              onChange={(e) => setSocketUrl(e.target.value)}
              className="w-full bg-input-bg rounded-md p-2 text-sm text-black placeholder:text-text-primary"
            />
          </div>
        </ChartCard>

        <ChartCard title="Notifications">
          <div className="space-y-2">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={notifications.email}
                onChange={(e) =>
                  setNotifications({ ...notifications, email: e.target.checked })
                }
              />
              Email
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={notifications.sms}
                onChange={(e) =>
                  setNotifications({ ...notifications, sms: e.target.checked })
                }
              />
              SMS
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={notifications.push}
                onChange={(e) =>
                  setNotifications({ ...notifications, push: e.target.checked })
                }
              />
              Push
            </label>
          </div>
        </ChartCard>

        <ChartCard title="Appearance & Language">
          <div className="space-y-2 flex flex-col">
            <div className="flex items-center gap-2">
              <ThemeToggle />
              <HighContrastToggle />
              <FontSizeSelector />
            </div>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value as 'en' | 'ko')}
              className="w-full bg-input-bg rounded-md p-2 text-sm text-black focus:outline-none focus:ring-2 focus:ring-accent"
              aria-label="Language"
            >
              <option value="en">English</option>
              <option value="ko">Korean</option>
            </select>
          </div>
        </ChartCard>

        <button
          onClick={saveSettings}
          className="px-4 py-2 bg-primary text-white rounded"
          type="button"
        >
          Save Settings
        </button>
      </div>
    </DashboardLayout>
  )
}
