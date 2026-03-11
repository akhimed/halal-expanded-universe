<script setup lang="ts">
import type { OwnerClaimStatus, ReportType, RestaurantDetail } from '~/types/api'
import { formatDistanceKm } from '~/utils/location'
import { claimStatusMeta, formatAllergenPresence, getPrimaryPhotoUrl } from '~/utils/restaurantDetail'

const route = useRoute()
const api = useApiClient()
const auth = useAuth()
const favorites = useFavorites()

auth.hydrate()

const loading = ref(true)
const errorMessage = ref('')
const restaurant = ref<RestaurantDetail | null>(null)

const searchExplanation = computed(() => {
  const value = route.query.explanation
  if (typeof value === 'string') return value
  if (Array.isArray(value) && value.length > 0) return value[0]
  return ''
})

const searchDistanceKm = computed(() => {
  const value = route.query.distance_km
  const parsed = typeof value === 'string' ? Number(value) : Array.isArray(value) ? Number(value[0]) : Number.NaN
  return Number.isFinite(parsed) ? parsed : null
})

const searchDistanceLabel = computed(() => formatDistanceKm(searchDistanceKm.value))

const isReportModalOpen = ref(false)
const reportType = ref<ReportType>('outdated_info')
const reportDescription = ref('')
const reportEvidenceUrl = ref('')
const reportSubmitting = ref(false)
const reportFeedback = ref<{ type: 'success' | 'error'; message: string } | null>(null)

const isClaimModalOpen = ref(false)
const claimNotes = ref('')
const claimSubmitting = ref(false)
const claimFeedback = ref<{ type: 'success' | 'error'; message: string } | null>(null)

const loadRestaurant = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const id = Number(route.params.id)
    restaurant.value = await api.getRestaurantById(id)
    if (auth.isAuthenticated.value) {
      await favorites.refreshFavorites()
    }
  } catch (error) {
    errorMessage.value = api.humanizeError(error, 'Unable to load restaurant details.')
  } finally {
    loading.value = false
  }
}

onMounted(loadRestaurant)

const toggleFavorite = async () => {
  if (!restaurant.value) return
  try {
    await favorites.toggleFavorite({
      id: restaurant.value.id,
      name: restaurant.value.name,
      description: restaurant.value.description,
      address: restaurant.value.address,
      latitude: restaurant.value.latitude,
      longitude: restaurant.value.longitude
    })
  } catch {
    errorMessage.value = 'Please login to save favorites.'
  }
}

const resetReportForm = () => {
  reportType.value = 'outdated_info'
  reportDescription.value = ''
  reportEvidenceUrl.value = ''
}

const closeReportModal = () => {
  isReportModalOpen.value = false
}

const openReportModal = () => {
  reportFeedback.value = null
  isReportModalOpen.value = true
}

const submitReport = async () => {
  if (!restaurant.value) return
  if (!auth.isAuthenticated.value) {
    reportFeedback.value = { type: 'error', message: 'Please login before submitting a report.' }
    return
  }

  reportSubmitting.value = true
  reportFeedback.value = null

  try {
    await api.submitRestaurantReport(restaurant.value.id, {
      report_type: reportType.value,
      description: reportDescription.value.trim() || undefined,
      evidence_url: reportEvidenceUrl.value.trim() || undefined
    })
    reportFeedback.value = {
      type: 'success',
      message: 'Thanks. Your report was submitted and will be reviewed by moderators.'
    }
    resetReportForm()
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to submit report. Please try again.'
    reportFeedback.value = { type: 'error', message }
  } finally {
    reportSubmitting.value = false
  }
}

const openClaimModal = () => {
  claimFeedback.value = null
  isClaimModalOpen.value = true
}

const closeClaimModal = () => {
  isClaimModalOpen.value = false
}

const trustLevelTone = computed(() => {
  const level = restaurant.value?.trust_breakdown?.trust_level
  if (level === 'high') return 'bg-emerald-100 text-emerald-800 border-emerald-200'
  if (level === 'medium') return 'bg-amber-100 text-amber-800 border-amber-200'
  return 'bg-rose-100 text-rose-800 border-rose-200'
})

const trustCaveats = computed(() => {
  const caveats = restaurant.value?.trust_breakdown?.caveats
  return Array.isArray(caveats) ? caveats : []
})

const trustRows = computed(() => {
  const breakdown = restaurant.value?.trust_breakdown
  if (!breakdown) return []
  return [
    { key: 'Base weighted score', value: breakdown.base_score },
    { key: 'Owner verification submitted', value: breakdown.owner_verification_submitted },
    { key: 'Moderation approval bonus', value: breakdown.moderation_approval },
    { key: 'Contradiction penalty', value: breakdown.contradiction_penalty },
    { key: 'Trust events delta', value: breakdown.event_delta },
    { key: 'Final trust score', value: breakdown.final_score }
  ]
})

const claimStatus = computed<OwnerClaimStatus | null>(() => restaurant.value?.owner_claim_status ?? null)

const claimState = computed(() => claimStatusMeta(claimStatus.value))
const primaryPhotoUrl = computed(() => getPrimaryPhotoUrl(restaurant.value))

const submitClaim = async () => {
  if (!restaurant.value) return
  if (!auth.isAuthenticated.value) {
    claimFeedback.value = { type: 'error', message: 'Please login before submitting a claim.' }
    return
  }

  claimSubmitting.value = true
  claimFeedback.value = null

  try {
    await api.submitOwnerClaim(restaurant.value.id, { notes: claimNotes.value.trim() || undefined })
    claimFeedback.value = {
      type: 'success',
      message: 'Claim submitted. You can track status in Owner Dashboard.'
    }
    claimNotes.value = ''
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to submit claim. Please try again.'
    claimFeedback.value = { type: 'error', message }
  } finally {
    claimSubmitting.value = false
  }
}
</script>

<template>
  <section>
    <div v-if="loading" class="rounded-lg border bg-white p-6 text-sm text-slate-600 shadow-sm">
      <p class="font-medium">Loading restaurant...</p>
      <p class="mt-1 text-xs text-slate-500">Preparing trust and verification details.</p>
    </div>

    <div v-else-if="errorMessage" class="rounded-lg border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700 shadow-sm">
      <p class="font-medium">Could not load this restaurant.</p>
      <p class="mt-1">{{ errorMessage }}</p>
      <button class="mt-4 rounded-md border border-rose-300 bg-white px-3 py-1.5 text-xs font-medium" @click="loadRestaurant">
        Retry
      </button>
    </div>

    <article v-else-if="restaurant" class="space-y-6 rounded-xl border bg-white p-4 shadow-sm sm:p-6">
      <header class="space-y-4 border-b pb-5">
        <div class="flex flex-col gap-4 md:flex-row md:justify-between">
          <div>
            <h1 class="text-2xl font-bold">{{ restaurant.name }}</h1>
            <p class="text-sm text-slate-600">{{ restaurant.address || 'Address unavailable' }}</p>
            <p v-if="searchDistanceLabel" class="mt-2 text-xs text-slate-500">Distance from your search: {{ searchDistanceLabel }}</p>
          </div>
          <div class="flex flex-wrap items-start gap-2">
            <button
              class="rounded-md border px-3 py-1 text-xs"
              :class="favorites.isFavorited(restaurant.id) ? 'border-amber-300 bg-amber-50 text-amber-700' : 'text-slate-700 hover:bg-slate-100'"
              @click="toggleFavorite"
            >
              {{ favorites.isFavorited(restaurant.id) ? 'Saved' : 'Save' }}
            </button>
            <button
              class="rounded-md border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs text-indigo-700 hover:bg-indigo-100"
              @click="openClaimModal"
            >
              Claim this listing
            </button>
            <button
              class="rounded-md border border-rose-200 bg-rose-50 px-3 py-1 text-xs text-rose-700 hover:bg-rose-100"
              @click="openReportModal"
            >
              Report listing
            </button>
          </div>
        </div>

        <p class="text-sm text-slate-700">{{ restaurant.description || 'No description available yet. Help improve this listing by reporting missing details.' }}</p>
        <p v-if="searchExplanation" class="rounded-md border border-indigo-100 bg-indigo-50 px-3 py-2 text-xs text-indigo-900">
          Why this matched: {{ searchExplanation }}
        </p>
      </header>

      <div class="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <section class="space-y-4 lg:col-span-2">
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div class="rounded-lg border bg-emerald-50 p-3 text-sm">
              <p class="text-xs text-emerald-700">Certification trust</p>
              <p class="text-lg font-semibold text-emerald-900">{{ restaurant.certification_score }}</p>
            </div>
            <div class="rounded-lg border bg-indigo-50 p-3 text-sm">
              <p class="text-xs text-indigo-700">Community verification</p>
              <p class="text-lg font-semibold text-indigo-900">{{ restaurant.community_verification_score }}</p>
            </div>
            <div class="rounded-lg border bg-amber-50 p-3 text-sm">
              <p class="text-xs text-amber-700">Recency</p>
              <p class="text-lg font-semibold text-amber-900">{{ restaurant.recency_score }}</p>
            </div>
          </div>

          <div class="rounded-lg border bg-slate-50 p-4">
            <h2 class="font-semibold">Dietary tags</h2>
            <div class="mt-2 flex flex-wrap gap-2">
              <span v-for="tag in restaurant.tags" :key="tag.tag" class="rounded-full bg-emerald-100 px-2 py-1 text-xs text-emerald-900">
                {{ tag.tag }}
              </span>
              <span v-if="restaurant.tags.length === 0" class="rounded-md border border-dashed px-3 py-2 text-sm text-slate-500">
                No dietary tags yet.
              </span>
            </div>
          </div>

          <div class="rounded-lg border bg-slate-50 p-4">
            <h2 class="font-semibold">Allergen information</h2>
            <ul class="mt-2 space-y-2 text-sm text-slate-700">
              <li
                v-for="item in restaurant.allergen_info"
                :key="item.allergen"
                class="flex items-center justify-between rounded-md bg-white px-3 py-2"
              >
                <span class="font-medium">{{ item.allergen }}</span>
                <span>{{ formatAllergenPresence(item.present) }}</span>
              </li>
              <li v-if="restaurant.allergen_info.length === 0" class="rounded-md border border-dashed px-3 py-2 text-slate-500">
                No allergen details have been provided.
              </li>
            </ul>
          </div>

          <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div class="rounded-lg border bg-slate-50 p-4">
              <div class="flex flex-wrap items-center justify-between gap-2">
                <h2 class="font-semibold">Trust details</h2>
                <span class="rounded-full border px-3 py-1 text-xs font-semibold capitalize" :class="trustLevelTone">
                  {{ restaurant.trust_breakdown?.trust_level || 'unknown' }} trust
                </span>
              </div>
              <p class="mt-2 text-xs text-slate-600">
                Deterministic trust combines weighted scores with verification and moderation events.
              </p>
              <ul v-if="trustRows.length > 0" class="mt-3 space-y-1 text-sm text-slate-700">
                <li v-for="row in trustRows" :key="row.key" class="flex items-center justify-between gap-4 rounded-md bg-white px-2 py-1">
                  <span class="font-medium">{{ row.key }}</span>
                  <span>{{ row.value }}</span>
                </li>
              </ul>
              <p v-else class="mt-3 rounded-md border border-dashed bg-white px-3 py-2 text-sm text-slate-500">
                Trust breakdown is not available yet.
              </p>
              <div v-if="trustCaveats.length > 0" class="mt-3 rounded-md border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
                <p class="font-semibold">Warnings and caveats</p>
                <ul class="mt-1 list-disc pl-4">
                  <li v-for="caveat in trustCaveats" :key="caveat">{{ caveat }}</li>
                </ul>
              </div>
            </div>

            <div class="space-y-4">
              <div class="rounded-lg border bg-slate-50 p-4">
                <h2 class="font-semibold">Owner claim state</h2>
                <p class="mt-2 inline-flex rounded-full border px-3 py-1 text-xs font-semibold" :class="claimState.tone">
                  {{ claimState.label }}
                </p>
                <p class="mt-3 text-xs text-slate-600">Owners can claim this listing and submit verification documents for review.</p>
              </div>

              <div class="rounded-lg border bg-slate-50 p-4">
                <h2 class="font-semibold">Report actions</h2>
                <p class="mt-2 text-xs text-slate-600">
                  Spot outdated dietary, allergen, or certification details? Submit a report for moderator review.
                </p>
                <button
                  class="mt-3 rounded-md border border-rose-200 bg-rose-50 px-3 py-1.5 text-xs text-rose-700 hover:bg-rose-100"
                  @click="openReportModal"
                >
                  Submit a report
                </button>
              </div>
            </div>
          </div>
        </section>

        <aside class="space-y-4">
          <div class="overflow-hidden rounded-lg border bg-slate-50">
            <img
              v-if="primaryPhotoUrl"
              :src="primaryPhotoUrl"
              :alt="`${restaurant.name} photo`"
              class="h-52 w-full object-cover"
            >
            <div v-else class="flex h-52 items-center justify-center bg-slate-100 px-4 text-center text-sm text-slate-500">
              No photo uploaded yet.
            </div>
          </div>

          <ClientOnly>
            <RestaurantLocationMap
              :latitude="restaurant.latitude"
              :longitude="restaurant.longitude"
              :name="restaurant.name"
            />
          </ClientOnly>
        </aside>
      </div>
    </article>

    <div v-else class="rounded-lg border bg-white p-6 text-sm text-slate-600 shadow-sm">
      Restaurant not found.
    </div>

    <div v-if="isClaimModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
      <div class="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl">
        <div class="mb-4 flex items-start justify-between gap-3">
          <div>
            <h2 class="text-lg font-semibold">Claim this listing</h2>
            <p class="text-sm text-slate-600">Submit ownership claim for moderator review.</p>
          </div>
          <button class="rounded-md border px-2 py-1 text-xs text-slate-600" @click="closeClaimModal">Close</button>
        </div>

        <div class="space-y-4">
          <label class="block text-sm">
            <span class="mb-1 block font-medium text-slate-700">Notes (optional)</span>
            <textarea
              v-model="claimNotes"
              rows="3"
              class="w-full rounded-md border px-3 py-2 text-sm"
              placeholder="Business name, role, and any verification context"
            />
          </label>

          <p
            v-if="claimFeedback"
            class="rounded-md px-3 py-2 text-sm"
            :class="claimFeedback.type === 'success' ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'"
          >
            {{ claimFeedback.message }}
          </p>

          <button
            class="w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="claimSubmitting"
            @click="submitClaim"
          >
            {{ claimSubmitting ? 'Submitting...' : 'Submit ownership claim' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="isReportModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
      <div class="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl">
        <div class="mb-4 flex items-start justify-between gap-3">
          <div>
            <h2 class="text-lg font-semibold">Report inaccurate listing</h2>
            <p class="text-sm text-slate-600">Help us keep restaurant information reliable.</p>
          </div>
          <button class="rounded-md border px-2 py-1 text-xs text-slate-600" @click="closeReportModal">Close</button>
        </div>

        <div class="space-y-4">
          <label class="block text-sm">
            <span class="mb-1 block font-medium text-slate-700">Report type</span>
            <select v-model="reportType" class="w-full rounded-md border px-3 py-2 text-sm">
              <option value="inaccurate_halal_status">Inaccurate halal status</option>
              <option value="inaccurate_kosher_status">Inaccurate kosher status</option>
              <option value="allergen_risk">Allergen risk</option>
              <option value="alcohol_served">Alcohol served</option>
              <option value="outdated_info">Outdated info</option>
              <option value="other">Other</option>
            </select>
          </label>

          <label class="block text-sm">
            <span class="mb-1 block font-medium text-slate-700">Description (optional)</span>
            <textarea
              v-model="reportDescription"
              rows="3"
              class="w-full rounded-md border px-3 py-2 text-sm"
              placeholder="What looks inaccurate?"
            />
          </label>

          <label class="block text-sm">
            <span class="mb-1 block font-medium text-slate-700">Evidence URL (optional, upload flow coming later)</span>
            <input
              v-model="reportEvidenceUrl"
              type="url"
              class="w-full rounded-md border px-3 py-2 text-sm"
              placeholder="https://example.com/photo-or-proof"
            >
          </label>

          <p
            v-if="reportFeedback"
            class="rounded-md px-3 py-2 text-sm"
            :class="reportFeedback.type === 'success' ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'"
          >
            {{ reportFeedback.message }}
          </p>

          <button
            class="w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="reportSubmitting"
            @click="submitReport"
          >
            {{ reportSubmitting ? 'Submitting...' : 'Submit report' }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>
