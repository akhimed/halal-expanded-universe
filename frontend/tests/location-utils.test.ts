import { describe, expect, it } from 'vitest'

import { formatDistanceKm, haversineDistanceKm } from '../utils/location'

describe('location helpers', () => {
  it('formats distance for display', () => {
    expect(formatDistanceKm(2)).toBe('2.0 km')
    expect(formatDistanceKm(12.345)).toBe('12.3 km')
  })

  it('returns null when distance is missing', () => {
    expect(formatDistanceKm(undefined)).toBeNull()
    expect(formatDistanceKm(null)).toBeNull()
  })

  it('computes haversine distance in kilometers', () => {
    const torontoToMississauga = haversineDistanceKm(43.6532, -79.3832, 43.589, -79.6441)
    expect(torontoToMississauga).toBeGreaterThan(20)
    expect(torontoToMississauga).toBeLessThan(30)
  })
})
