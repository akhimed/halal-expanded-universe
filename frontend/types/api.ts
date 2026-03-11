export type SearchProfile = 'balanced' | 'strict' | 'community_first'
export type UserRole = 'user' | 'owner' | 'moderator' | 'admin'
export type ReportType =
  | 'inaccurate_halal_status'
  | 'inaccurate_kosher_status'
  | 'allergen_risk'
  | 'alcohol_served'
  | 'outdated_info'
  | 'other'
export type OwnerClaimStatus = 'pending' | 'approved' | 'rejected'
export type ModerationReportStatus = 'open' | 'under_review' | 'resolved' | 'rejected'

export interface AuthUser {
  id: number
  email: string
  display_name: string
  role: UserRole
  created_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: 'bearer'
  user: AuthUser
}

export interface RestaurantSummary {
  id: number
  name: string
  description: string | null
  address: string | null
  latitude: number | null
  longitude: number | null
}

export interface ExcludedAllergenStatus {
  allergen: string
  present: boolean
}


export interface GroupParticipantInput {
  participant_name: string
  required_tags: string[]
  excluded_allergens: string[]
  profile: SearchProfile
}

export interface ParticipantSatisfaction {
  participant_name: string
  required_tags_satisfied: boolean
  missing_required_tags: string[]
  excluded_allergens_satisfied: boolean
  conflicting_allergens: string[]
  profile: SearchProfile
  participant_fit_score: number
}

export interface SearchResult {
  restaurant: RestaurantSummary
  matched_tags: string[]
  excluded_allergen_status: ExcludedAllergenStatus[]
  trust_score: number
  distance_km?: number | null
  trust_level: 'high' | 'medium' | 'low'
  trust_caveats: string[]
  group_fit_score?: number | null
  participant_satisfaction: ParticipantSatisfaction[]
  explanation: string
  full_explanation: string
}

export interface SearchLocation {
  query: string
  label: string
  latitude: number
  longitude: number
}

export interface SearchResponse {
  results: SearchResult[]
  search_location?: SearchLocation | null
}


export interface TrustBreakdown {
  base_score: number
  score_band: string
  score_band_label: string
  owner_verification_submitted: number
  moderation_approval: number
  contradiction_penalty: number
  event_delta: number
  recency_component: number
  final_score: number
  trust_level: 'high' | 'medium' | 'low'
  low_confidence: boolean
  caveats: string[]
}

export interface RestaurantDetail {
  id: number
  name: string
  description: string | null
  address: string | null
  latitude: number | null
  longitude: number | null
  certification_score: number
  community_verification_score: number
  recency_score: number
  trust_breakdown?: TrustBreakdown
  tags: { tag: string }[]
  allergen_info: { allergen: string; present: boolean }[]
}

export interface FavoritesResponse {
  favorites: RestaurantSummary[]
}

export interface ReportResponse {
  id: number
  restaurant_id: number | null
  report_type: ReportType | null
  description: string | null
  evidence_url: string | null
  status: string
  created_at: string
}

export interface OwnerClaimResponse {
  id: number
  user_id: number
  restaurant_id: number
  status: OwnerClaimStatus
  notes: string | null
  created_at: string
}

export interface OwnerDashboardClaim {
  id: number
  status: OwnerClaimStatus
  notes: string | null
  created_at: string
  restaurant: RestaurantSummary
}

export interface OwnerDashboardResponse {
  claims: OwnerDashboardClaim[]
}

export interface VerificationDocument {
  id: number
  owner_user_id: number
  restaurant_id: number
  owner_claim_id: number
  document_type: string
  original_filename: string | null
  storage_path: string | null
  mime_type: string | null
  notes: string | null
  status: 'pending' | 'approved' | 'rejected'
  reviewed_by_user_id: number | null
  reviewed_at: string | null
  created_at: string
}

export interface VerificationDocumentsResponse {
  documents: VerificationDocument[]
  pagination?: { total: number; limit: number; offset: number }
}

export interface ModerationReportsResponse {
  reports: ModerationReportItem[]
  pagination?: { total: number; limit: number; offset: number }
}

export interface ModerationOwnerClaimsResponse {
  claims: ModerationOwnerClaimItem[]
  pagination?: { total: number; limit: number; offset: number }
}

export interface ModerationReportItem {
  id: number
  user_id: number | null
  restaurant_id: number | null
  report_type: string | null
  description: string | null
  evidence_url: string | null
  status: ModerationReportStatus
  created_at: string
}

export interface ModerationOwnerClaimItem {
  id: number
  user_id: number
  restaurant_id: number
  status: OwnerClaimStatus
  notes: string | null
  created_at: string
}
