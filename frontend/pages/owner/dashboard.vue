<script setup lang="ts">
import type { OwnerDashboardClaim, VerificationDocument } from '~/types/api'

definePageMeta({
  middleware: ['auth'],
  requiresAuth: true
})

const api = useApiClient()
const auth = useAuth()

auth.hydrate()

const loading = ref(true)
const errorMessage = ref('')
const claims = ref<OwnerDashboardClaim[]>([])
const documents = ref<VerificationDocument[]>([])
const actionMessage = ref('')
const selectedStatus = ref<'all' | 'pending' | 'approved' | 'rejected'>('all')
const pendingModerationTotal = ref(0)

const formByClaim = ref<Record<number, { document_type: string; notes: string; certification_type: 'halal' | 'kosher'; file: File | null }>>({})

const initFormForClaim = (claimId: number) => {
  if (!formByClaim.value[claimId]) {
    formByClaim.value[claimId] = {
      document_type: 'business_license',
      notes: '',
      certification_type: 'halal',
      file: null
    }
  }
}

const loadData = async () => {
  try {
    const [dashboard, ownerDocs] = await Promise.all([api.getOwnerDashboard(), api.listOwnerVerificationDocuments()])
    claims.value = dashboard.claims
    pendingModerationTotal.value = dashboard.pending_moderation_total
    documents.value = ownerDocs.documents
    claims.value.forEach((claim) => initFormForClaim(claim.id))
  } catch (error) {
    errorMessage.value = api.humanizeError(error, 'Failed to load owner dashboard.')
  } finally {
    loading.value = false
  }
}

onMounted(loadData)

const onFileSelect = (claimId: number, event: Event) => {
  const target = event.target as HTMLInputElement
  formByClaim.value[claimId].file = target.files?.[0] || null
}

const submitDoc = async (claimId: number) => {
  const form = formByClaim.value[claimId]
  if (!form) return

  const payload = new FormData()
  payload.append('document_type', form.document_type)
  if (form.notes.trim()) payload.append('notes', form.notes.trim())
  if (form.file) payload.append('file', form.file)

  try {
    await api.submitVerificationDocument(claimId, payload)
    actionMessage.value = `Verification document submitted for claim #${claimId}.`
    form.notes = ''
    form.file = null
    const ownerDocs = await api.listOwnerVerificationDocuments()
    documents.value = ownerDocs.documents
  } catch (error) {
    actionMessage.value = api.humanizeError(error, 'Failed to submit verification document.')
  }
}

const submitCertificationEvidence = async (claimId: number) => {
  const form = formByClaim.value[claimId]
  if (!form) return
  const payload = new FormData()
  payload.append('certification_type', form.certification_type)
  if (form.notes.trim()) payload.append('notes', form.notes.trim())
  if (form.file) payload.append('file', form.file)

  try {
    await api.submitCertificationEvidence(claimId, payload)
    actionMessage.value = `${form.certification_type.toUpperCase()} certification evidence submitted for claim #${claimId}.`
    form.notes = ''
    form.file = null
    const ownerDocs = await api.listOwnerVerificationDocuments()
    documents.value = ownerDocs.documents
  } catch (error) {
    actionMessage.value = api.humanizeError(error, 'Failed to submit certification evidence.')
  }
}

const statusClass = (status: string) => {
  if (status === 'approved') return 'bg-emerald-50 text-emerald-700 border-emerald-200'
  if (status === 'rejected') return 'bg-rose-50 text-rose-700 border-rose-200'
  return 'bg-amber-50 text-amber-700 border-amber-200'
}

const claimsByStatus = computed(() => ({
  pending: claims.value.filter((claim) => claim.status === 'pending').length,
  approved: claims.value.filter((claim) => claim.status === 'approved').length,
  rejected: claims.value.filter((claim) => claim.status === 'rejected').length
}))

const filteredClaims = computed(() => {
  if (selectedStatus.value === 'all') return claims.value
  return claims.value.filter((claim) => claim.status === selectedStatus.value)
})

const docsByClaim = computed(() => {
  const grouped: Record<number, VerificationDocument[]> = {}
  documents.value.forEach((doc) => {
    if (!grouped[doc.owner_claim_id]) grouped[doc.owner_claim_id] = []
    grouped[doc.owner_claim_id].push(doc)
  })
  return grouped
})

const formatDate = (value: string) => new Date(value).toLocaleString()
</script>

<template>
  <section class="space-y-4">
    <div class="rounded-xl border bg-white p-6 shadow-sm">
      <h1 class="text-2xl font-bold">Owner Dashboard</h1>
      <p class="mt-2 text-slate-600">Track claims, trust score, evidence status, and moderation queues.</p>
      <p class="mt-1 text-sm text-slate-500">Signed in as: {{ auth.user?.display_name }} ({{ auth.user?.role }})</p>

      <div class="mt-4 grid gap-3 sm:grid-cols-5">
        <div class="rounded-lg border bg-slate-50 p-3">
          <p class="text-xs uppercase text-slate-500">Total claims</p>
          <p class="text-xl font-semibold">{{ claims.length }}</p>
        </div>
        <div class="rounded-lg border bg-amber-50 p-3">
          <p class="text-xs uppercase text-amber-700">Pending</p>
          <p class="text-xl font-semibold text-amber-800">{{ claimsByStatus.pending }}</p>
        </div>
        <div class="rounded-lg border bg-emerald-50 p-3">
          <p class="text-xs uppercase text-emerald-700">Approved</p>
          <p class="text-xl font-semibold text-emerald-800">{{ claimsByStatus.approved }}</p>
        </div>
        <div class="rounded-lg border bg-rose-50 p-3">
          <p class="text-xs uppercase text-rose-700">Rejected</p>
          <p class="text-xl font-semibold text-rose-800">{{ claimsByStatus.rejected }}</p>
        </div>
        <div class="rounded-lg border bg-blue-50 p-3">
          <p class="text-xs uppercase text-blue-700">Pending moderation</p>
          <p class="text-xl font-semibold text-blue-800">{{ pendingModerationTotal }}</p>
        </div>
      </div>
    </div>

    <div v-if="loading" class="rounded-lg border bg-white p-6 text-sm text-slate-600">Loading owner dashboard...</div>
    <div v-else-if="errorMessage" class="rounded-lg border bg-white p-6 text-sm text-red-600">{{ errorMessage }}</div>

    <template v-else>
      <p v-if="actionMessage" class="rounded-lg border bg-white p-3 text-sm text-slate-700">{{ actionMessage }}</p>

      <section class="rounded-xl border bg-white p-5 shadow-sm">
        <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h2 class="text-lg font-semibold">Your Claims</h2>
          <select v-model="selectedStatus" class="rounded-md border px-2 py-1 text-sm">
            <option value="all">All statuses</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>

        <div v-if="claims.length === 0" class="text-sm text-slate-600">No owner claims yet.</div>
        <div v-else-if="filteredClaims.length === 0" class="text-sm text-slate-600">No claims match this status.</div>

        <div v-else class="space-y-4">
          <article v-for="claim in filteredClaims" :key="claim.id" class="rounded-lg border p-4">
            <div class="flex items-start justify-between gap-3">
              <div>
                <NuxtLink :to="`/restaurants/${claim.restaurant.id}`" class="font-semibold text-emerald-700 hover:underline">
                  {{ claim.restaurant.name }}
                </NuxtLink>
                <p class="text-xs text-slate-500">Claim #{{ claim.id }} · {{ claim.restaurant.address || 'Address unavailable' }}</p>
                <p class="text-xs text-slate-500">Submitted: {{ formatDate(claim.created_at) }}</p>
                <p class="text-xs text-slate-700">Trust score: <span class="font-semibold">{{ claim.trust_score.toFixed(3) }}</span> ({{ claim.trust_level }})</p>
                <p class="text-xs text-slate-700">
                  Evidence status: pending {{ claim.evidence_status.pending }} · approved {{ claim.evidence_status.approved }} · rejected {{ claim.evidence_status.rejected }}
                </p>
              </div>
              <span class="rounded-full border px-2 py-1 text-xs" :class="statusClass(claim.status)">{{ claim.status }}</span>
            </div>

            <p v-if="claim.notes" class="mt-2 text-sm text-slate-700">Your note: {{ claim.notes }}</p>

            <div class="mt-2 rounded-md border bg-blue-50 p-2 text-sm" v-if="claim.pending_moderation_items.length">
              <p class="font-medium text-blue-800">Pending moderation items</p>
              <ul class="ml-4 list-disc text-blue-700">
                <li v-for="item in claim.pending_moderation_items" :key="item">{{ item }}</li>
              </ul>
            </div>

            <div v-if="docsByClaim[claim.id]?.length" class="mt-3 rounded-md border bg-slate-50 p-3">
              <p class="mb-2 text-sm font-medium">Submitted verification documents</p>
              <ul class="space-y-1 text-sm text-slate-700">
                <li v-for="doc in docsByClaim[claim.id]" :key="doc.id">#{{ doc.id }} · {{ doc.document_type }} · <span class="font-medium">{{ doc.status }}</span></li>
              </ul>
            </div>

            <div class="mt-3 rounded-md bg-slate-50 p-3">
              <p class="mb-2 text-sm font-medium">Upload verification document</p>
              <div class="grid gap-2 md:grid-cols-2">
                <select v-model="formByClaim[claim.id].document_type" class="rounded border px-2 py-1 text-sm">
                  <option value="business_license">Business license</option>
                  <option value="owner_id">Owner ID</option>
                  <option value="other">Other</option>
                </select>
                <input type="file" class="rounded border px-2 py-1 text-sm" @change="onFileSelect(claim.id, $event)" />
              </div>
              <textarea v-model="formByClaim[claim.id].notes" class="mt-2 w-full rounded border px-2 py-1 text-sm" rows="2" placeholder="notes" />
              <button class="mt-2 rounded border px-3 py-1 text-xs hover:bg-slate-100" @click="submitDoc(claim.id)">Submit verification document</button>
            </div>

            <div class="mt-3 rounded-md bg-emerald-50 p-3">
              <p class="mb-2 text-sm font-medium">Upload halal / kosher certification evidence</p>
              <div class="grid gap-2 md:grid-cols-2">
                <select v-model="formByClaim[claim.id].certification_type" class="rounded border px-2 py-1 text-sm">
                  <option value="halal">Halal</option>
                  <option value="kosher">Kosher</option>
                </select>
                <input type="file" class="rounded border px-2 py-1 text-sm" @change="onFileSelect(claim.id, $event)" />
              </div>
              <button class="mt-2 rounded border px-3 py-1 text-xs hover:bg-emerald-100" @click="submitCertificationEvidence(claim.id)">Submit certification evidence</button>
            </div>
          </article>
        </div>
      </section>
    </template>
  </section>
</template>
