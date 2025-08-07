'use client'

import { useState, useEffect } from 'react'
import { BellIcon, XMarkIcon, SpeakerWaveIcon, SpeakerXMarkIcon } from '@heroicons/react/24/outline'

interface NotificationData {
  id: number
  device_id: string
  sensor_id: string
  alert_type: string
  anomaly_type: string
  severity: string
  message: string
  sensor_value?: number
  threshold_value?: number
  created_at: string
  tts_message: string
}

interface NotificationPanelProps {
  notifications: NotificationData[]
  onClose?: () => void
}

const severityColors = {
  critical: 'bg-red-500',
  high: 'bg-orange-500',
  medium: 'bg-yellow-500',
  low: 'bg-green-500'
}

const severityLabels = {
  critical: '치명적',
  high: '높음',
  medium: '보통',
  low: '낮음'
}

export default function NotificationPanel({ notifications, onClose }: NotificationPanelProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isTTSEnabled, setIsTTSEnabled] = useState(true)
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    if (notifications.length > 0) {
      setUnreadCount(prev => prev + 1)
      setIsOpen(true)
    }
  }, [notifications])

  const handleClose = () => {
    setIsOpen(false)
    setUnreadCount(0)
    onClose?.()
  }

  const toggleTTS = () => {
    setIsTTSEnabled(!isTTSEnabled)
  }

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleString('ko-KR', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (!isOpen) return null

  return (
    <div className="fixed top-4 right-4 z-50 w-96 max-h-96 overflow-hidden">
      <div className="bg-white rounded-lg shadow-xl border border-gray-200">
        {/* 헤더 */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center space-x-2">
            <BellIcon className="h-5 w-5 text-red-500" />
            <h3 className="text-lg font-semibold">실시간 알림</h3>
            {unreadCount > 0 && (
              <span className="bg-red-500 text-white text-xs rounded-full px-2 py-1">
                {unreadCount}
              </span>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={toggleTTS}
              className="p-1 rounded hover:bg-gray-100"
              title={isTTSEnabled ? 'TTS 비활성화' : 'TTS 활성화'}
            >
              {isTTSEnabled ? (
                <SpeakerWaveIcon className="h-4 w-4 text-blue-500" />
              ) : (
                <SpeakerXMarkIcon className="h-4 w-4 text-gray-400" />
              )}
            </button>
            <button
              onClick={handleClose}
              className="p-1 rounded hover:bg-gray-100"
            >
              <XMarkIcon className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* 알림 목록 */}
        <div className="max-h-80 overflow-y-auto">
          {notifications.length === 0 ? (
            <div className="p-4 text-center text-gray-500">
              새로운 알림이 없습니다
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {notifications.map((notification) => (
                <div
                  key={notification.id}
                  className="p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start space-x-3">
                    <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${severityColors[notification.severity as keyof typeof severityColors]}`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium text-gray-900">
                          {notification.device_id}
                        </p>
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          notification.severity === 'critical' ? 'bg-red-100 text-red-800' :
                          notification.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                          notification.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-green-100 text-green-800'
                        }`}>
                          {severityLabels[notification.severity as keyof typeof severityLabels]}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">
                        {notification.anomaly_type}
                      </p>
                      <p className="text-sm text-gray-500 mt-1">
                        {notification.message}
                      </p>
                      {notification.sensor_value && (
                        <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                          <span>센서값: {notification.sensor_value.toFixed(2)}</span>
                          {notification.threshold_value && (
                            <span>임계값: {notification.threshold_value.toFixed(2)}</span>
                          )}
                        </div>
                      )}
                      <p className="text-xs text-gray-400 mt-2">
                        {formatTime(notification.created_at)}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 푸터 */}
        <div className="p-3 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>총 {notifications.length}개의 알림</span>
            <span>TTS: {isTTSEnabled ? '활성' : '비활성'}</span>
          </div>
        </div>
      </div>
    </div>
  )
} 