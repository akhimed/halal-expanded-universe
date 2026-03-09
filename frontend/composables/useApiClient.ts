import type {
  AuthResponse,
  AuthUser,
  FavoritesResponse,
  ModerationOwnerClaimsResponse,
  ModerationOwnerClaimItem,
  ModerationReportsResponse,
  ModerationReportItem,
  OwnerClaimResponse,
  OwnerDashboardResponse,
  ReportResponse,
  ReportType,
  RestaurantDetail,
  GroupParticipantInput,
  SearchProfile,
  SearchResponse,
  VerificationDocument,
  VerificationDocumentsResponse
} from '~/types/api'

export const useApiClient = () => {
  const config = useRuntimeConfig()
  const baseURL = config.public.apiBaseUrl
  const auth = useAuth()

  const authHeaders = () =>
    auth.token.value
      ? {
          Authorization: `Bearer ${auth.token.value}`
        }
      : undefined

  const getHealth = async () => {
    return await $fetch<{ ok: boolean; service: string }>(`${baseURL}/health`)
  }

  const humanizeError = (error: unknown, fallback: string) => {
    const data = (error as any)?.data
    if (data?.error?.message) return data.error.message as string
    if (typeof (error as any)?.message === 'string') return (error as any).message as string
    return fallback
  }

  const register = async (payload: { email: string; display_name: string; password: string }) => {
    return await $fetch<AuthResponse>(`${baseURL}/auth/register`, {
      method: 'POST',
      body: payload
    })
  }

  const login = async (payload: { email: string; password: string }) => {
    return await $fetch<AuthResponse>(`${baseURL}/auth/login`, {
      method: 'POST',
      body: payload
    })
  }

  const getCurrentUser = async () => {
    return await $fetch<AuthUser>(`${baseURL}/auth/me`, {
      headers: authHeaders()
    })
  }

  const listFavorites = async () => {
    return await $fetch<FavoritesResponse>(`${baseURL}/favorites`, {
      headers: authHeaders()
    })
  }

  const saveFavorite = async (restaurantId: number) => {
    return await $fetch<{ status: string; restaurant_id: number }>(`${baseURL}/favorites/${restaurantId}`, {
      method: 'POST',
      headers: authHeaders()
    })
  }

  const removeFavorite = async (restaurantId: number) => {
    return await $fetch<{ status: string; restaurant_id: number }>(`${baseURL}/favorites/${restaurantId}`, {
      method: 'DELETE',
      headers: authHeaders()
    })
  }

  const submitOwnerClaim = async (restaurantId: number, payload: { notes?: string }) => {
    return await $fetch<OwnerClaimResponse>(`${baseURL}/restaurants/${restaurantId}/claims`, {
      method: 'POST',
      headers: authHeaders(),
      body: payload
    })
  }

  const getOwnerDashboard = async () => {
    return await $fetch<OwnerDashboardResponse>(`${baseURL}/owner/dashboard`, {
      headers: authHeaders()
    })
  }

  const listOwnerVerificationDocuments = async () => {
    return await $fetch<VerificationDocumentsResponse>(`${baseURL}/owner/verification-documents`, {
      headers: authHeaders()
    })
  }

  const submitVerificationDocument = async (claimId: number, payload: FormData) => {
    return await $fetch<VerificationDocument>(`${baseURL}/owner/claims/${claimId}/verification-documents`, {
      method: 'POST',
      headers: authHeaders(),
      body: payload
    })
  }

  const listModerationReports = async (params?: { limit?: number; offset?: number }) => {
    return await $fetch<ModerationReportsResponse>(`${baseURL}/moderation/reports`, {
      query: params,
      headers: authHeaders()
    })
  }

  const updateModerationReport = async (reportId: number, payload: { status: string; note?: string }) => {
    return await $fetch<ModerationReportItem>(`${baseURL}/moderation/reports/${reportId}`, {
      method: 'PATCH',
      headers: authHeaders(),
      body: payload
    })
  }

  const listModerationOwnerClaims = async (params?: { limit?: number; offset?: number }) => {
    return await $fetch<ModerationOwnerClaimsResponse>(`${baseURL}/moderation/owner-claims`, {
      query: params,
      headers: authHeaders()
    })
  }

  const updateModerationOwnerClaim = async (claimId: number, payload: { status: 'approved' | 'rejected'; note?: string }) => {
    return await $fetch<ModerationOwnerClaimItem>(`${baseURL}/moderation/owner-claims/${claimId}`, {
      method: 'PATCH',
      headers: authHeaders(),
      body: payload
    })
  }

  const listModerationVerificationDocuments = async (params?: { limit?: number; offset?: number }) => {
    return await $fetch<VerificationDocumentsResponse>(`${baseURL}/moderation/verification-documents`, {
      query: params,
      headers: authHeaders()
    })
  }

  const updateModerationVerificationDocument = async (
    documentId: number,
    payload: { status: 'approved' | 'rejected'; note?: string }
  ) => {
    return await $fetch<VerificationDocument>(`${baseURL}/moderation/verification-documents/${documentId}`, {
      method: 'PATCH',
      headers: authHeaders(),
      body: payload
    })
  }

  const submitRestaurantReport = async (
    restaurantId: number,
    payload: { report_type: ReportType; description?: string; evidence_url?: string }
  ) => {
    return await $fetch<ReportResponse>(`${baseURL}/restaurants/${restaurantId}/reports`, {
      method: 'POST',
      headers: authHeaders(),
      body: payload
    })
  }

  const searchRestaurants = async (payload: {
    required_tags: string[]
    excluded_allergens: string[]
    profile: SearchProfile
    group_mode?: boolean
    participants?: GroupParticipantInput[]
  }) => {
    return await $fetch<SearchResponse>(`${baseURL}/search`, {
      method: 'POST',
      body: payload
    })
  }

  const getRestaurantById = async (id: number) => {
    return await $fetch<RestaurantDetail>(`${baseURL}/restaurants/${id}`)
  }

  return {
    getHealth,
    register,
    login,
    getCurrentUser,
    listFavorites,
    saveFavorite,
    removeFavorite,
    submitOwnerClaim,
    getOwnerDashboard,
    listOwnerVerificationDocuments,
    submitVerificationDocument,
    listModerationReports,
    updateModerationReport,
    listModerationOwnerClaims,
    updateModerationOwnerClaim,
    listModerationVerificationDocuments,
    updateModerationVerificationDocument,
    submitRestaurantReport,
    searchRestaurants,
    getRestaurantById,
    humanizeError
  }
}
