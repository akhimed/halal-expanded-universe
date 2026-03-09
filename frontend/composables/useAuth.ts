import type { AuthResponse, AuthUser } from '~/types/api'

const TOKEN_KEY = 'faithdiet_token'
const USER_KEY = 'faithdiet_user'

export const useAuth = () => {
  const token = useState<string | null>('auth_token', () => null)
  const user = useState<AuthUser | null>('auth_user', () => null)

  const hydrate = () => {
    if (!process.client) return
    if (!token.value) token.value = localStorage.getItem(TOKEN_KEY)
    if (!user.value) {
      const raw = localStorage.getItem(USER_KEY)
      user.value = raw ? JSON.parse(raw) : null
    }
  }

  const setSession = (payload: AuthResponse) => {
    token.value = payload.access_token
    user.value = payload.user
    if (process.client) {
      localStorage.setItem(TOKEN_KEY, payload.access_token)
      localStorage.setItem(USER_KEY, JSON.stringify(payload.user))
    }
  }

  const logout = () => {
    token.value = null
    user.value = null
    if (process.client) {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    }
  }

  const isAuthenticated = computed(() => !!token.value)

  return { token, user, isAuthenticated, hydrate, setSession, logout }
}
