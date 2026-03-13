<script setup lang="ts">
import type { ModerationOwnerClaimItem, ModerationReportItem, TrustEvidenceItem, VerificationDocument } from '~/types/api'

definePageMeta({ middleware: ['auth'], requiresAuth: true })

const api = useApiClient()
const auth = useAuth()
auth.hydrate()

const loading = ref(true)
const errorMessage = ref('')
const actionFeedback = ref('')
const reports = ref<ModerationReportItem[]>([])
const claims = ref<ModerationOwnerClaimItem[]>([])
const verificationDocs = ref<VerificationDocument[]>([])
const trustEvidence = ref<TrustEvidenceItem[]>([])

const isModerator = computed(() => ['moderator', 'admin'].includes(auth.user.value?.role || ''))

const statusClass = (status: string) => {
  if (status === 'approved' || status === 'resolved') return 'bg-emerald-50 text-emerald-700 border-emerald-200'
  if (status === 'rejected') return 'bg-rose-50 text-rose-700 border-rose-200'
  if (status === 'under_review') return 'bg-blue-50 text-blue-700 border-blue-200'
  return 'bg-amber-50 text-amber-700 border-amber-200'
}

const loadQueues = async () => {
  if (!isModerator.value) {
    errorMessage.value = 'Moderator/Admin role required.'
    loading.value = false
    return
  }
  loading.value = true
  try {
    const [r, c, d, e] = await Promise.all([
      api.listModerationReports(),
      api.listModerationOwnerClaims(),
      api.listModerationVerificationDocuments(),
      api.listModerationTrustEvidence()
    ])
    reports.value = r.reports
    claims.value = c.claims
    verificationDocs.value = d.documents
    trustEvidence.value = e.evidence
  } catch (error) {
    errorMessage.value = api.humanizeError(error, 'Failed to load moderation queues.')
  } finally {
    loading.value = false
  }
}

const updateReportStatus = async (id: number, status: string) => {
  await api.updateModerationReport(id, { status })
  actionFeedback.value = `Report ${id} -> ${status}`
  await loadQueues()
}

const updateClaimStatus = async (id: number, status: 'approved' | 'rejected') => {
  await api.updateModerationOwnerClaim(id, { status })
  actionFeedback.value = `Claim ${id} -> ${status}`
  await loadQueues()
}

const updateDocumentStatus = async (id: number, status: 'approved' | 'rejected') => {
  await api.updateModerationVerificationDocument(id, { status })
  actionFeedback.value = `Document ${id} -> ${status}`
  await loadQueues()
}

const updateEvidenceStatus = async (id: number, status: 'approved' | 'rejected') => {
  await api.updateModerationTrustEvidence(id, { status })
  actionFeedback.value = `Evidence ${id} -> ${status}`
  await loadQueues()
}

onMounted(loadQueues)
</script>

<template>
  <section class="space-y-6">
    <div class="rounded-xl border bg-white p-6 shadow-sm">
      <h1 class="text-2xl font-bold">Admin / Moderator Dashboard</h1>
      <p class="mt-2 text-slate-600">Moderate reports, owner claims, verification documents, and trust evidence.</p>
    </div>

    <div v-if="loading" class="rounded-lg border bg-white p-6 text-sm text-slate-600">Loading moderation queues...</div>
    <div v-else-if="errorMessage" class="rounded-lg border bg-white p-6 text-sm text-red-600">{{ errorMessage }}</div>
    <template v-else>
      <p v-if="actionFeedback" class="rounded-lg border bg-white p-3 text-sm">{{ actionFeedback }}</p>

      <section class="rounded-xl border bg-white p-5 shadow-sm">
        <h2 class="text-lg font-semibold">Trust Evidence Queue</h2>
        <div v-if="trustEvidence.length === 0" class="mt-2 text-sm text-slate-600">No trust evidence entries.</div>
        <div v-else class="mt-3 space-y-3">
          <article v-for="item in trustEvidence" :key="item.id" class="rounded-lg border p-3">
            <div class="flex items-center justify-between">
              <p class="font-medium">#{{ item.id }} · {{ item.evidence_type }} · {{ item.claim_key }}</p>
              <span class="rounded-full border px-2 py-1 text-xs" :class="statusClass(item.status)">{{ item.status }}</span>
            </div>
            <p class="text-xs text-slate-500">Restaurant {{ item.restaurant_id }} · {{ item.source_label || 'unknown source' }}</p>
            <div class="mt-2 flex gap-2">
              <button class="rounded border px-2 py-1 text-xs" @click="updateEvidenceStatus(item.id, 'approved')">Approve</button>
              <button class="rounded border px-2 py-1 text-xs" @click="updateEvidenceStatus(item.id, 'rejected')">Reject</button>
            </div>
          </article>
        </div>
      </section>

      <section class="rounded-xl border bg-white p-5 shadow-sm">
        <h2 class="text-lg font-semibold">Reports Queue</h2>
        <div v-if="reports.length === 0" class="mt-2 text-sm text-slate-600">No reports.</div>
        <div v-else class="mt-3 space-y-2">
          <article v-for="report in reports" :key="report.id" class="rounded border p-2 text-sm">
            <p>#{{ report.id }} · {{ report.report_type || 'other' }}</p>
            <div class="mt-2 flex gap-2">
              <button class="rounded border px-2 py-1 text-xs" @click="updateReportStatus(report.id, 'under_review')">Under review</button>
              <button class="rounded border px-2 py-1 text-xs" @click="updateReportStatus(report.id, 'resolved')">Resolve</button>
            </div>
          </article>
        </div>
      </section>

      <section class="rounded-xl border bg-white p-5 shadow-sm">
        <h2 class="text-lg font-semibold">Owner Claims Queue</h2>
        <div v-if="claims.length === 0" class="mt-2 text-sm text-slate-600">No owner claims.</div>
        <div v-else class="mt-3 space-y-2">
          <article v-for="claim in claims" :key="claim.id" class="rounded border p-2 text-sm">
            <p>#{{ claim.id }} · restaurant {{ claim.restaurant_id }}</p>
            <div class="mt-2 flex gap-2">
              <button class="rounded border px-2 py-1 text-xs" @click="updateClaimStatus(claim.id, 'approved')">Approve</button>
              <button class="rounded border px-2 py-1 text-xs" @click="updateClaimStatus(claim.id, 'rejected')">Reject</button>
            </div>
          </article>
        </div>
      </section>

      <section class="rounded-xl border bg-white p-5 shadow-sm">
        <h2 class="text-lg font-semibold">Verification Documents Queue</h2>
        <div v-if="verificationDocs.length === 0" class="mt-2 text-sm text-slate-600">No verification docs.</div>
        <div v-else class="mt-3 space-y-2">
          <article v-for="doc in verificationDocs" :key="doc.id" class="rounded border p-2 text-sm">
            <p>#{{ doc.id }} · claim {{ doc.owner_claim_id }} · {{ doc.document_type }}</p>
            <div class="mt-2 flex gap-2">
              <button class="rounded border px-2 py-1 text-xs" @click="updateDocumentStatus(doc.id, 'approved')">Approve</button>
              <button class="rounded border px-2 py-1 text-xs" @click="updateDocumentStatus(doc.id, 'rejected')">Reject</button>
            </div>
          </article>
        </div>
      </section>
    </template>
  </section>
</template>
