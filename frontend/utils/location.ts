export const formatDistanceKm = (distanceKm: number | null | undefined) => {
  if (distanceKm === null || distanceKm === undefined || Number.isNaN(distanceKm)) {
    return null
  }
  return `${distanceKm.toFixed(1)} km`
}
