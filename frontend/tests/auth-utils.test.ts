import { describe, expect, it } from 'vitest'

import { buildLoginRedirectPath, getPostAuthRedirect } from '../utils/auth'

describe('auth redirect helpers', () => {
  it('builds login path with encoded redirect', () => {
    expect(buildLoginRedirectPath('/favorites')).toBe('/login?redirect=%2Ffavorites')
    expect(buildLoginRedirectPath('/restaurants/12?tab=reviews')).toBe('/login?redirect=%2Frestaurants%2F12%3Ftab%3Dreviews')
  })

  it('returns safe post-auth redirect destination', () => {
    expect(getPostAuthRedirect('/favorites')).toBe('/favorites')
    expect(getPostAuthRedirect('https://example.com')).toBe('/favorites')
    expect(getPostAuthRedirect(undefined)).toBe('/favorites')
  })
})
