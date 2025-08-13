// 클라이언트에서만 사용되는 상태 저장소
'use client'
import { create } from 'zustand'

// 허용되는 사용자 역할 타입 정의
export type UserRole = 'Admin' | 'Engineer' | 'Viewer'

// 스토어에서 관리할 상태와 액션 타입
interface AuthState {
  role: UserRole
  setRole: (role: UserRole) => void
}

// 사용자 역할을 저장하는 간단한 zustand 스토어
export const useAuthStore = create<AuthState>((set) => ({
  role: 'Admin',
  setRole: (role) => set({ role }),
}))
