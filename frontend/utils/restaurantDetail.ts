import type { OwnerClaimStatus, RestaurantDetail } from '~/types/api'

export const getPrimaryPhotoUrl = (restaurant: RestaurantDetail | null): string | null => {
  if (!restaurant) return null

  const firstPhoto = restaurant.photos?.find((photo) => typeof photo.url === 'string' && photo.url.trim().length > 0)
  if (firstPhoto) return firstPhoto.url

  if (typeof restaurant.photo_url === 'string' && restaurant.photo_url.trim().length > 0) {
    return restaurant.photo_url
  }

  return null
}

export const formatAllergenPresence = (present: boolean): string => (present ? 'Present' : 'Not present')

export const claimStatusMeta = (status: OwnerClaimStatus | null) => {
  if (status === 'approved') {
    return {
      label: 'Claim approved',
      tone: 'border-emerald-200 bg-emerald-50 text-emerald-800'
    }
  }

  if (status === 'rejected') {
    return {
      label: 'Claim rejected',
      tone: 'border-rose-200 bg-rose-50 text-rose-800'
    }
  }

  if (status === 'pending') {
    return {
      label: 'Claim pending review',
      tone: 'border-amber-200 bg-amber-50 text-amber-800'
    }
  }

  return {
    label: 'Not yet claimed',
    tone: 'border-slate-200 bg-slate-50 text-slate-700'
  }
}
