<script setup lang="ts">
import type { ReportType, RestaurantDetail } from '~/types/api'

const route = useRoute()
const api = useApiClient()
const auth = useAuth()
const favorites = useFavorites()

auth.hydrate()

const loading = ref(true)
const errorMessage = ref('')
const restaurant = ref<RestaurantDetail | null>(null)

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

onMounted(async () => {
  try {
    const id = Number(route.params.id)
    restaurant.value = await api.getRestaurantById(id)
    if (auth.isAuthenticated.value) {
      await favorites.refreshFavorites()
    }
  } catch (error) {
    errorMessage.value = String(error)
  } finally {
    loading.value = false
  }
})

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
    <div v-if="loading" class="rounded-lg border bg-white p-6 text-sm text-slate-600">Loading restaurant...</div>
    <div v-else-if="errorMessage" class="rounded-lg border bg-white p-6 text-sm text-red-600">{{ errorMessage }}</div>

    <article v-else-if="restaurant" class="space-y-4 rounded-xl border bg-white p-6 shadow-sm">
      <div class="flex items-start justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold">{{ restaurant.name }}</h1>
          <p class="text-sm text-slate-600">{{ restaurant.address || 'Address unavailable' }}</p>
        </div>
        <div class="flex flex-wrap items-center justify-end gap-2">
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

      <p class="text-slate-700">{{ restaurant.description || 'No description available.' }}</p>

      <ClientOnly>
        <RestaurantLocationMap
          :latitude="restaurant.latitude"
          :longitude="restaurant.longitude"
          :name="restaurant.name"
        />
      </ClientOnly>

      <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div class="rounded-lg bg-slate-50 p-3 text-sm">Certification: {{ restaurant.certification_score }}</div>
        <div class="rounded-lg bg-slate-50 p-3 text-sm">Community: {{ restaurant.community_verification_score }}</div>
        <div class="rounded-lg bg-slate-50 p-3 text-sm">Recency: {{ restaurant.recency_score }}</div>
      </div>


      <div v-if="restaurant.trust_breakdown" class="rounded-lg border bg-slate-50 p-4">
        <h2 class="font-semibold">Trust Breakdown</h2>
        <ul class="mt-2 grid grid-cols-1 gap-1 text-sm text-slate-700 md:grid-cols-2">
          <li v-for="(value, key) in restaurant.trust_breakdown" :key="key">
            <span class="font-medium">{{ key }}:</span> {{ value }}
          </li>
        </ul>
      </div>

      <div>
        <h2 class="font-semibold">Tags</h2>
        <div class="mt-2 flex flex-wrap gap-2">
          <span v-for="tag in restaurant.tags" :key="tag.tag" class="rounded-full bg-emerald-100 px-2 py-1 text-xs">
            {{ tag.tag }}
          </span>
        </div>
      </div>

      <div>
        <h2 class="font-semibold">Allergen Info</h2>
        <ul class="mt-2 space-y-1 text-sm text-slate-700">
          <li v-for="item in restaurant.allergen_info" :key="item.allergen">
            {{ item.allergen }}: {{ item.present ? 'present' : 'not present' }}
          </li>
        </ul>
      </div>
    </article>

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
            />
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
