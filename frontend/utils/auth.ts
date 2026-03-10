export const buildLoginRedirectPath = (destination: string) => {
  const redirect = encodeURIComponent(destination || '/favorites')
  return `/login?redirect=${redirect}`
}

export const getPostAuthRedirect = (redirect: unknown) => {
  if (typeof redirect !== 'string' || !redirect.startsWith('/')) return '/favorites'
  return redirect
}
