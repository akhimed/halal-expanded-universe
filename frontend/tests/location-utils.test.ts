import { describe, expect, it } from 'vitest'

import { formatDistanceKm } from '../utils/location'

describe('location helpers', () => {
  it('formats distance for display', () => {
    expect(formatDistanceKm(2)).toBe('2.0 km')
    expect(formatDistanceKm(12.345)).toBe('12.3 km')
  })

  it('returns null when distance is missing', () => {
    expect(formatDistanceKm(undefined)).toBeNull()
    expect(formatDistanceKm(null)).toBeNull()
  })
})
