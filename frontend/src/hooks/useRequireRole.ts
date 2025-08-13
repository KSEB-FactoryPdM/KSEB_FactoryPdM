// 클라이언트 전용 훅 선언
'use client'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { useAuthStore, UserRole } from '@/store/useAuthStore'

// 특정 역할을 요구하는 페이지에서 사용
export function useRequireRole(roles: UserRole | UserRole[]) {
  const router = useRouter()
  // 현재 사용자 역할을 상태에서 가져옴
  const role = useAuthStore((s) => s.role)

  useEffect(() => {
    // 허용된 역할 배열을 만든 후 권한이 없으면 리다이렉트
    const allowed = Array.isArray(roles) ? roles : [roles]
    if (!allowed.includes(role)) {
      router.replace('/monitoring')
    }
  }, [roles, role, router])
}
