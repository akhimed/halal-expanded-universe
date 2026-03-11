export const formatDistanceKm = (distanceKm: number | null | undefined) => {
  if (distanceKm === null || distanceKm === undefined || Number.isNaN(distanceKm)) {
    return null
  }
  return `${distanceKm.toFixed(1)} km`
}

export const haversineDistanceKm = (
  originLatitude: number,
  originLongitude: number,
  destinationLatitude: number,
  destinationLongitude: number
) => {
  const earthRadiusKm = 6371
  const dLat = ((destinationLatitude - originLatitude) * Math.PI) / 180
  const dLon = ((destinationLongitude - originLongitude) * Math.PI) / 180
  const lat1 = (originLatitude * Math.PI) / 180
  const lat2 = (destinationLatitude * Math.PI) / 180

  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) * Math.sin(dLon / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))

  return earthRadiusKm * c
}
