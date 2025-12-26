/**
 * 认证状态管理
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '../types'

interface AuthState {
  token: string | null
  user: User | null
  setToken: (token: string) => void
  setUser: (user: User) => void
  logout: () => void
  isAuthenticated: () => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,

      setToken: (token: string) => set({ token }),

      setUser: (user: User) => set({ user }),

      logout: () => {
        set({ token: null, user: null })
        localStorage.removeItem('token')
        localStorage.removeItem('user')
      },

      isAuthenticated: () => !!get().token,
    }),
    {
      name: 'auth-storage',
    }
  )
)
