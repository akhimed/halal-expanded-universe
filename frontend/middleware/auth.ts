import { buildLoginRedirectPath } from '~/utils/auth'
import type { AuthUser } from '~/types/api'

export default defineNuxtRouteMiddleware(async (to) => {
  if (process.server) return

  const auth = useAuth()
  auth.hydrate()

  const requiresAuth = to.meta.requiresAuth === true
  if (!requiresAuth) return

  if (!auth.isAuthenticated.value) {
    return navigateTo(buildLoginRedirectPath(to.fullPath))
  }

  if (!auth.user.value) {
    const config = useRuntimeConfig()
    try {
      const me = await $fetch<AuthUser>(`${config.public.apiBaseUrl}/auth/me`, {
        headers: { Authorization: `Bearer ${auth.token.value}` }
      })
      auth.user.value = me
    } catch {
      auth.logout()
      return navigateTo(buildLoginRedirectPath(to.fullPath))
    }
  }
})
