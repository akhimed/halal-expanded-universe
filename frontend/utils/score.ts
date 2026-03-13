export const scoreToPercent = (score: number | null | undefined): number | null => {
  if (typeof score !== 'number' || Number.isNaN(score)) return null
  const normalized = Math.max(0, Math.min(1, score))
  return Math.round(normalized * 100)
}
