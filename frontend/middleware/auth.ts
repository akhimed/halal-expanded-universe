export default defineNuxtRouteMiddleware((to) => {
  if (process.server) return

  const auth = useAuth()
  auth.hydrate()

  const requiresAuth = to.meta.requiresAuth === true
  if (requiresAuth && !auth.isAuthenticated.value) {
    return navigateTo('/login')
  }
})
