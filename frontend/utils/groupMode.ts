import type { GroupParticipantInput, ParticipantSatisfaction, SearchResult } from '~/types/api'

export const DEFAULT_PARTICIPANT_PROFILE = 'balanced' as const

export function createParticipant(nextNumber: number): GroupParticipantInput {
  return {
    participant_name: `Participant ${nextNumber}`,
    required_tags: [],
    excluded_allergens: [],
    profile: DEFAULT_PARTICIPANT_PROFILE
  }
}

export function participantReadiness(participant: GroupParticipantInput): string[] {
  const guidance: string[] = []
  if (participant.required_tags.length === 0) {
    guidance.push('Add at least one required tag for clearer matching')
  }
  if (participant.excluded_allergens.length === 0) {
    guidance.push('Add excluded allergens if safety checks are needed')
  }
  return guidance
}

export function summarizeParticipantSatisfaction(participant: ParticipantSatisfaction): {
  fitLabel: 'Strong fit' | 'Partial fit' | 'Poor fit'
  fitClass: string
  tradeoffSummary: string
} {
  const fitScore = participant.participant_fit_score
  const hasTagTradeoff = !participant.required_tags_satisfied
  const hasAllergenTradeoff = !participant.excluded_allergens_satisfied

  if (fitScore >= 0.8 && !hasTagTradeoff && !hasAllergenTradeoff) {
    return {
      fitLabel: 'Strong fit',
      fitClass: 'text-emerald-700 bg-emerald-50 border-emerald-200',
      tradeoffSummary: 'No meaningful tradeoffs for this participant.'
    }
  }

  if (fitScore >= 0.5) {
    return {
      fitLabel: 'Partial fit',
      fitClass: 'text-amber-700 bg-amber-50 border-amber-200',
      tradeoffSummary: [
        hasTagTradeoff ? `Missing tags: ${participant.missing_required_tags.join(', ') || 'none listed'}.` : '',
        hasAllergenTradeoff ? `Allergen conflicts: ${participant.conflicting_allergens.join(', ') || 'none listed'}.` : ''
      ]
        .filter(Boolean)
        .join(' ')
    }
  }

  return {
    fitLabel: 'Poor fit',
    fitClass: 'text-rose-700 bg-rose-50 border-rose-200',
    tradeoffSummary: [
      hasTagTradeoff ? `Missing tags: ${participant.missing_required_tags.join(', ') || 'none listed'}.` : '',
      hasAllergenTradeoff ? `Allergen conflicts: ${participant.conflicting_allergens.join(', ') || 'none listed'}.` : ''
    ]
      .filter(Boolean)
      .join(' ')
  }
}

export function summarizeGroupTradeoffs(result: SearchResult): {
  participants: number
  strongFits: number
  participantsWithTradeoffs: number
  headline: string
} {
  const participants = result.participant_satisfaction.length
  if (participants === 0) {
    return {
      participants: 0,
      strongFits: 0,
      participantsWithTradeoffs: 0,
      headline: 'Individual mode result.'
    }
  }

  const strongFits = result.participant_satisfaction.filter((participant) => {
    const summary = summarizeParticipantSatisfaction(participant)
    return summary.fitLabel === 'Strong fit'
  }).length
  const participantsWithTradeoffs = participants - strongFits

  return {
    participants,
    strongFits,
    participantsWithTradeoffs,
    headline:
      participantsWithTradeoffs === 0
        ? 'All participants are strongly satisfied.'
        : `${participantsWithTradeoffs} participant(s) have tradeoffs to review.`
  }
}
