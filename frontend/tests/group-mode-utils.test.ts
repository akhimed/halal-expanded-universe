import { describe, expect, it } from 'vitest'
import {
  createParticipant,
  participantReadiness,
  summarizeGroupTradeoffs,
  summarizeParticipantSatisfaction
} from '../utils/groupMode'

describe('group mode helpers', () => {
  it('creates deterministic default participants', () => {
    expect(createParticipant(2)).toEqual({
      participant_name: 'Participant 2',
      required_tags: [],
      excluded_allergens: [],
      profile: 'balanced'
    })
  })

  it('shows setup guidance for missing participant constraints', () => {
    const tips = participantReadiness(createParticipant(1))
    expect(tips).toContain('Add at least one required tag for clearer matching')
    expect(tips).toContain('Add excluded allergens if safety checks are needed')
  })

  it('summarizes participant fit with explainable labels', () => {
    const summary = summarizeParticipantSatisfaction({
      participant_name: 'A',
      required_tags_satisfied: false,
      missing_required_tags: ['halal'],
      excluded_allergens_satisfied: true,
      conflicting_allergens: [],
      profile: 'strict',
      participant_fit_score: 0.65
    })

    expect(summary.fitLabel).toBe('Partial fit')
    expect(summary.tradeoffSummary).toContain('Missing tags: halal.')
  })

  it('summarizes group tradeoffs using participant outcomes', () => {
    const summary = summarizeGroupTradeoffs({
      restaurant: { id: 1, name: 'Demo', description: null, address: null, latitude: null, longitude: null },
      matched_tags: [],
      excluded_allergen_status: [],
      trust_score: 0.75,
      trust_level: 'medium',
      trust_caveats: [],
      group_fit_score: 0.7,
      participant_satisfaction: [
        {
          participant_name: 'A',
          required_tags_satisfied: true,
          missing_required_tags: [],
          excluded_allergens_satisfied: true,
          conflicting_allergens: [],
          profile: 'balanced',
          participant_fit_score: 0.92
        },
        {
          participant_name: 'B',
          required_tags_satisfied: false,
          missing_required_tags: ['vegan'],
          excluded_allergens_satisfied: true,
          conflicting_allergens: [],
          profile: 'balanced',
          participant_fit_score: 0.6
        }
      ],
      explanation: 'x',
      full_explanation: 'y'
    })

    expect(summary.participants).toBe(2)
    expect(summary.strongFits).toBe(1)
    expect(summary.participantsWithTradeoffs).toBe(1)
  })
})
