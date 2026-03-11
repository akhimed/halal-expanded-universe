import { describe, expect, it } from 'vitest'

import type { RestaurantDetail } from '../types/api'
import { claimStatusMeta, formatAllergenPresence, getPrimaryPhotoUrl } from '../utils/restaurantDetail'

const baseRestaurant: RestaurantDetail = {
  id: 1,
  name: 'Test Restaurant',
  description: null,
  address: null,
  latitude: null,
  longitude: null,
  certification_score: 0.6,
  community_verification_score: 0.5,
  recency_score: 0.8,
  tags: [],
  allergen_info: []
}

describe('restaurant detail helpers', () => {
  it('picks first photo url when available', () => {
    const detail: RestaurantDetail = {
      ...baseRestaurant,
      photos: [{ url: '' }, { url: 'https://img.example.com/photo.jpg' }],
      photo_url: 'https://img.example.com/fallback.jpg'
    }

    expect(getPrimaryPhotoUrl(detail)).toBe('https://img.example.com/photo.jpg')
  })

  it('falls back to photo_url and null for missing photo values', () => {
    expect(getPrimaryPhotoUrl({ ...baseRestaurant, photo_url: 'https://img.example.com/fallback.jpg' })).toBe(
      'https://img.example.com/fallback.jpg'
    )
    expect(getPrimaryPhotoUrl(baseRestaurant)).toBeNull()
  })

  it('formats claim status metadata', () => {
    expect(claimStatusMeta('approved').label).toBe('Claim approved')
    expect(claimStatusMeta('pending').label).toBe('Claim pending review')
    expect(claimStatusMeta('rejected').label).toBe('Claim rejected')
    expect(claimStatusMeta(null).label).toBe('Not yet claimed')
  })

  it('formats allergen presence labels', () => {
    expect(formatAllergenPresence(true)).toBe('Present')
    expect(formatAllergenPresence(false)).toBe('Not present')
  })
})
