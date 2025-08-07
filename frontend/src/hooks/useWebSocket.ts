// 클라이언트 전용 훅임을 명시
'use client'

import { useEffect, useState } from 'react'
// 로깅 유틸리티
import { error } from '@/lib/logger'

// WebSocket 연결과 재연결 로직을 제공하는 커스텀 훅
export default function useWebSocket<T = unknown>(
  url?: string,
  {
    autoReconnect = false,
    maxRetries = 5,
    initialDelay = 1000,
    maxDelay = 30000,
  }: {
    autoReconnect?: boolean
    maxRetries?: number
    initialDelay?: number
    maxDelay?: number
  } = {}
) {
  // 서버로부터 받은 데이터를 저장할 상태
  const [data, setData] = useState<T | null>(null)
  // WebSocket 연결 상태 저장
  const [status, setStatus] = useState<'connecting' | 'connected' | 'error'>(
    url ? 'connecting' : 'error'
  )

  // WebSocket 연결을 관리하는 효과
  useEffect(() => {
    // URL이 없으면 아무것도 하지 않음
    if (!url) return

    // 실제 WebSocket 인스턴스와 재연결 카운트 관리 변수들
    let socket: WebSocket
    let retry = 0
    let reconnectTimer: NodeJS.Timeout | null = null
    let active = true

    // 연결이 열렸을 때 상태 갱신
    const handleOpen = () => {
      setStatus('connected')
    }

    // 서버로부터 메시지를 수신했을 때 데이터 파싱
    const handleMessage = (ev: MessageEvent) => {
      try {
        setData(JSON.parse(ev.data))
      } catch {
        // 파싱 에러는 무시
      }
    }

    // 에러 발생 시 상태 변경 후 소켓 종료
    const handleError = () => {
      setStatus('error')
      socket?.close()
    }

    // 연결이 닫힌 경우 재연결 로직 실행
    const handleClose = () => {
      if (active && autoReconnect && retry < maxRetries) {
        const delay = Math.min(initialDelay * 2 ** retry, maxDelay)
        retry += 1
        setStatus('connecting')
        reconnectTimer = setTimeout(connect, delay)
        // 타이머가 동작하지 않는 환경을 위해 즉시 재연결 시도
        connect()
      }
    }

    // 실제 WebSocket 연결을 생성하는 함수
    const connect = () => {
      setStatus('connecting')
      try {
        socket = new WebSocket(url)
      } catch (err) {
        error('WebSocket connection failed:', err)
        setStatus('error')
        return
      }
      socket.addEventListener('open', handleOpen)
      socket.addEventListener('message', handleMessage)
      socket.addEventListener('error', handleError)
      socket.addEventListener('close', handleClose)
    }

    // 초기 연결 시도
    connect()

    // 언마운트 시 연결 및 타이머 정리
    return () => {
      active = false
      if (reconnectTimer) clearTimeout(reconnectTimer)
      if (socket) {
        socket.removeEventListener('open', handleOpen)
        socket.removeEventListener('message', handleMessage)
        socket.removeEventListener('error', handleError)
        socket.removeEventListener('close', handleClose)
        socket.close()
      }
    }
  }, [url, autoReconnect, maxRetries, initialDelay, maxDelay])

  // 훅에서 데이터와 상태를 반환
  return { data, status }
}
