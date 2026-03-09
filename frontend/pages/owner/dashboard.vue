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

const formByClaim = ref<Record<number, { document_type: string; notes: string; metadata_filename: string; metadata_mime_type: string }>>({})

const initFormForClaim = (claimId: number) => {
  if (!formByClaim.value[claimId]) {
    formByClaim.value[claimId] = {
      document_type: 'business_license',
      notes: '',
      metadata_filename: '',
      metadata_mime_type: ''
    }
  }
}

const loadData = async () => {
  try {
    const [dashboard, ownerDocs] = await Promise.all([api.getOwnerDashboard(), api.listOwnerVerificationDocuments()])
    claims.value = dashboard.claims
    documents.value = ownerDocs.documents
    claims.value.forEach((claim) => initFormForClaim(claim.id))
  } catch (error) {
    errorMessage.value = api.humanizeError(error, 'Failed to load owner dashboard.')
  } finally {
    loading.value = false
  }
}

onMounted(loadData)

const submitDoc = async (claimId: number) => {
  const form = formByClaim.value[claimId]
  if (!form) return

  const payload = new FormData()
  payload.append('document_type', form.document_type)
  if (form.notes.trim()) payload.append('notes', form.notes.trim())
  if (form.metadata_filename.trim()) payload.append('metadata_filename', form.metadata_filename.trim())
  if (form.metadata_mime_type.trim()) payload.append('metadata_mime_type', form.metadata_mime_type.trim())

  try {
    await api.submitVerificationDocument(claimId, payload)
    actionMessage.value = `Verification document submitted for claim #${claimId}.`
    form.notes = ''
    form.metadata_filename = ''
    form.metadata_mime_type = ''
    const ownerDocs = await api.listOwnerVerificationDocuments()
    documents.value = ownerDocs.documents
  } catch (error) {
    actionMessage.value = api.humanizeError(error, 'Failed to submit verification document.')
  }
}

const statusClass = (status: string) => {
  if (status === 'approved') return 'bg-emerald-50 text-emerald-700 border-emerald-200'
  if (status === 'rejected') return 'bg-rose-50 text-rose-700 border-rose-200'
  return 'bg-amber-50 text-amber-700 border-amber-200'
}
</script>

<template>
  <section class="space-y-4">
    <div class="rounded-xl border bg-white p-6 shadow-sm">
      <h1 class="text-2xl font-bold">Owner Dashboard</h1>
      <p class="mt-2 text-slate-600">Track ownership claims and submit verification metadata/documents.</p>
      <p class="mt-1 text-sm text-slate-500">Signed in as: {{ auth.user?.display_name }} ({{ auth.user?.role }})</p>
    </div>

    <div v-if="loading" class="rounded-lg border bg-white p-6 text-sm text-slate-600">Loading owner dashboard...</div>
    <div v-else-if="errorMessage" class="rounded-lg border bg-white p-6 text-sm text-red-600">{{ errorMessage }}</div>

    <template v-else>
      <p v-if="actionMessage" class="rounded-lg border bg-white p-3 text-sm text-slate-700">{{ actionMessage }}</p>

      <section class="rounded-xl border bg-white p-5 shadow-sm">
        <h2 class="mb-3 text-lg font-semibold">Your Claims</h2>
        <div v-if="claims.length === 0" class="text-sm text-slate-600">
          No owner claims yet. Open a restaurant detail page and click <span class="font-semibold">Claim this listing</span>.
        </div>

        <div v-else class="space-y-4">
          <article v-for="claim in claims" :key="claim.id" class="rounded-lg border p-4">
            <div class="flex items-start justify-between gap-3">
              <div>
                <NuxtLink :to="`/restaurants/${claim.restaurant.id}`" class="font-semibold text-emerald-700 hover:underline">
                  {{ claim.restaurant.name }}
                </NuxtLink>
                <p class="text-xs text-slate-500">Claim #{{ claim.id }} · {{ claim.restaurant.address || 'Address unavailable' }}</p>
              </div>
              <span class="rounded-full border px-2 py-1 text-xs" :class="statusClass(claim.status)">{{ claim.status }}</span>
            </div>

            <div class="mt-3 rounded-md bg-slate-50 p-3">
              <p class="mb-2 text-sm font-medium">Submit verification document metadata</p>
              <div class="grid gap-2 md:grid-cols-2">
                <input v-model="formByClaim[claim.id].document_type" class="rounded border px-2 py-1 text-sm" placeholder="document type" />
                <input v-model="formByClaim[claim.id].metadata_filename" class="rounded border px-2 py-1 text-sm" placeholder="filename (optional)" />
              </div>
              <input
                v-model="formByClaim[claim.id].metadata_mime_type"
                class="mt-2 w-full rounded border px-2 py-1 text-sm"
                placeholder="mime type (optional)"
              />
              <textarea
                v-model="formByClaim[claim.id].notes"
                class="mt-2 w-full rounded border px-2 py-1 text-sm"
                rows="2"
                placeholder="notes"
              />
              <button class="mt-2 rounded border px-3 py-1 text-xs hover:bg-slate-100" @click="submitDoc(claim.id)">Submit verification metadata</button>
            </div>
          </article>
        </div>
      </section>

      <section class="rounded-xl border bg-white p-5 shadow-sm">
        <h2 class="mb-3 text-lg font-semibold">Submitted Verification Documents</h2>
        <div v-if="documents.length === 0" class="text-sm text-slate-600">No verification documents submitted yet.</div>
        <div v-else class="space-y-2">
          <article v-for="doc in documents" :key="doc.id" class="rounded-md border p-3 text-sm">
            <div class="flex items-center justify-between">
              <p class="font-medium">#{{ doc.id }} · claim {{ doc.owner_claim_id }} · {{ doc.document_type }}</p>
              <span class="rounded-full border px-2 py-1 text-xs" :class="statusClass(doc.status)">{{ doc.status }}</span>
            </div>
            <p class="text-slate-600">{{ doc.original_filename || 'metadata only' }}</p>
          </article>
        </div>
      </section>
    </template>
  </section>
</template>
