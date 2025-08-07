// 클라이언트 전용 훅임을 명시
'use client'

import { useState, useEffect, useRef, useCallback } from 'react'

interface WebSocketOptions {
  autoReconnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

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

interface WebSocketMessage {
  type: 'notification' | 'system' | 'data'
  timestamp: string
  data?: NotificationData | unknown
  message?: string
  message_type?: string
}

export default function useWebSocket<T = unknown>(
  url: string,
  options: WebSocketOptions = {}
): {
  data: T[] | null
  status: 'connecting' | 'connected' | 'error' | 'disconnected'
  sendMessage: (message: unknown) => void
  notifications: NotificationData[]
  playTTS: (message: string) => void
} {
  const [data, setData] = useState<T[] | null>(null)
  const [status, setStatus] = useState<'connecting' | 'connected' | 'error' | 'disconnected'>('connecting')
  const [notifications, setNotifications] = useState<NotificationData[]>([])
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = options.maxReconnectAttempts || 5
  const reconnectInterval = options.reconnectInterval || 3000

  // TTS 기능
  const playTTS = useCallback((message: string) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(message)
      utterance.lang = 'ko-KR'
      utterance.rate = 0.8
      utterance.pitch = 1.0
      utterance.volume = 0.8
      speechSynthesis.speak(utterance)
    }
  }, [])

  // 알림 처리
  const handleNotification = useCallback((notificationData: NotificationData) => {
    setNotifications(prev => [notificationData, ...prev.slice(0, 9)]) // 최대 10개 유지
    
    // TTS 재생
    if (notificationData.severity === 'critical' || notificationData.severity === 'high') {
      playTTS(notificationData.tts_message)
    }
    
    // 브라우저 알림
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('KSEB Factory 알림', {
        body: notificationData.message,
        icon: '/logo.svg',
        tag: `notification-${notificationData.id}`
      })
    }
  }, [playTTS])

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        setStatus('connected')
        reconnectAttempts.current = 0
        console.log('WebSocket 연결됨')
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          
          if (message.type === 'notification' && message.data) {
            handleNotification(message.data as NotificationData)
          } else if (message.type === 'data') {
            setData(prev => {
              if (!prev) return [message.data as T]
              return [...prev, message.data as T]
            })
          } else if (message.type === 'system') {
            console.log('시스템 메시지:', message.message)
          }
        } catch (error) {
          console.error('WebSocket 메시지 파싱 오류:', error)
        }
      }

      ws.onclose = () => {
        setStatus('disconnected')
        console.log('WebSocket 연결 끊김')
        
        if (options.autoReconnect && reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++
          setTimeout(connect, reconnectInterval)
        }
      }

      ws.onerror = (error) => {
        setStatus('error')
        console.error('WebSocket 오류:', error)
      }
    } catch (error) {
      setStatus('error')
      console.error('WebSocket 연결 실패:', error)
    }
  }, [url, options.autoReconnect, maxReconnectAttempts, reconnectInterval, handleNotification])

  const sendMessage = useCallback((message: unknown) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }, [])

  useEffect(() => {
    // 브라우저 알림 권한 요청
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }
    
    connect()

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [connect])

  return {
    data,
    status,
    sendMessage,
    notifications,
    playTTS
  }
}
