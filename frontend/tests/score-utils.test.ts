import { describe, expect, it } from 'vitest'
import { scoreToPercent } from '../utils/score'

describe('score utils', () => {
  it('normalizes decimal trust/group scores to percentages', () => {
    expect(scoreToPercent(0.905)).toBe(91)
    expect(scoreToPercent(0.5)).toBe(50)
  })

  it('clamps invalid out-of-range values', () => {
    expect(scoreToPercent(-1)).toBe(0)
    expect(scoreToPercent(2)).toBe(100)
  })

  it('returns null for missing or invalid inputs', () => {
    expect(scoreToPercent(null)).toBeNull()
    expect(scoreToPercent(undefined)).toBeNull()
    expect(scoreToPercent(Number.NaN)).toBeNull()
  })
})
