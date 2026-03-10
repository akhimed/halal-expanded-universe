<script setup lang="ts">
import type { ModerationOwnerClaimItem, ModerationReportItem, VerificationDocument } from '~/types/api'

definePageMeta({
  middleware: ['auth'],
  requiresAuth: true
})

const api = useApiClient()
const auth = useAuth()
auth.hydrate()

const loading = ref(true)
const errorMessage = ref('')
const reports = ref<ModerationReportItem[]>([])
const claims = ref<ModerationOwnerClaimItem[]>([])
const verificationDocs = ref<VerificationDocument[]>([])
const actionFeedback = ref('')
const pageSize = 20

const reportStatusFilter = ref<'all' | 'open' | 'under_review' | 'resolved' | 'rejected'>('all')
const claimStatusFilter = ref<'all' | 'pending' | 'approved' | 'rejected'>('all')
const verificationStatusFilter = ref<'all' | 'pending' | 'approved' | 'rejected'>('all')

const reportNotes = ref<Record<number, string>>({})
const claimNotes = ref<Record<number, string>>({})
const verificationNotes = ref<Record<number, string>>({})

const isModerator = computed(() => auth.user.value?.role === 'moderator' || auth.user.value?.role === 'admin')

const statusClass = (status: string) => {
  if (status === 'approved' || status === 'resolved') return 'bg-emerald-50 text-emerald-700 border-emerald-200'
  if (status === 'rejected') return 'bg-rose-50 text-rose-700 border-rose-200'
  if (status === 'under_review') return 'bg-blue-50 text-blue-700 border-blue-200'
  return 'bg-amber-50 text-amber-700 border-amber-200'
}

const filteredReports = computed(() => {
  if (reportStatusFilter.value === 'all') return reports.value
  return reports.value.filter((report) => report.status === reportStatusFilter.value)
})

const filteredClaims = computed(() => {
  if (claimStatusFilter.value === 'all') return claims.value
  return claims.value.filter((claim) => claim.status === claimStatusFilter.value)
})

const filteredVerificationDocs = computed(() => {
  if (verificationStatusFilter.value === 'all') return verificationDocs.value
  return verificationDocs.value.filter((doc) => doc.status === verificationStatusFilter.value)
})

const loadQueues = async () => {
  if (!isModerator.value) {
    errorMessage.value = 'Moderator/Admin role required.'
    loading.value = false
    return
  }

  loading.value = true
  errorMessage.value = ''
  actionFeedback.value = ''
  try {
    const [reportsRes, claimsRes, docsRes] = await Promise.all([
      api.listModerationReports({ limit: pageSize, offset: 0 }),
      api.listModerationOwnerClaims({ limit: pageSize, offset: 0 }),
      api.listModerationVerificationDocuments({ limit: pageSize, offset: 0 })
    ])
    reports.value = reportsRes.reports
    claims.value = claimsRes.claims
    verificationDocs.value = docsRes.documents
  } catch (error) {
    errorMessage.value = api.humanizeError(error, 'Failed to load moderation queues.')
  } finally {
    loading.value = false
  }
}

onMounted(loadQueues)

const updateReportStatus = async (report: ModerationReportItem, status: string) => {
  try {
    const note = reportNotes.value[report.id]?.trim() || undefined
    const updated = await api.updateModerationReport(report.id, { status, note })
    const target = reports.value.find((r) => r.id === report.id)
    if (target) target.status = updated.status
    actionFeedback.value = `Report #${report.id} updated to ${status}.`
  } catch (error) {
    actionFeedback.value = api.humanizeError(error, 'Failed to update report.')
  }
}

const updateClaimStatus = async (claim: ModerationOwnerClaimItem, status: 'approved' | 'rejected') => {
  try {
    const note = claimNotes.value[claim.id]?.trim() || undefined
    const updated = await api.updateModerationOwnerClaim(claim.id, { status, note })
    const target = claims.value.find((c) => c.id === claim.id)
    if (target) target.status = updated.status
    actionFeedback.value = `Claim #${claim.id} updated to ${status}.`
  } catch (error) {
    actionFeedback.value = api.humanizeError(error, 'Failed to update claim.')
  }
}

const updateVerificationStatus = async (doc: VerificationDocument, status: 'approved' | 'rejected') => {
  try {
    const note = verificationNotes.value[doc.id]?.trim() || undefined
    const updated = await api.updateModerationVerificationDocument(doc.id, { status, note })
    const target = verificationDocs.value.find((d) => d.id === doc.id)
    if (target) target.status = updated.status
    actionFeedback.value = `Verification document #${doc.id} updated to ${status}.`
  } catch (error) {
    actionFeedback.value = api.humanizeError(error, 'Failed to update verification document.')
  }
}
</script>

<template>
  <section class="space-y-6">
    <div class="rounded-xl border bg-white p-6 shadow-sm">
      <h1 class="text-2xl font-bold">Admin / Moderator Dashboard</h1>
      <p class="mt-2 text-slate-600">Moderate reports, owner claims, and verification documents.</p>

      <div class="mt-4 grid gap-3 sm:grid-cols-3">
        <div class="rounded-lg border bg-slate-50 p-3">
          <p class="text-xs uppercase text-slate-500">Reports</p>
          <p class="text-xl font-semibold">{{ reports.length }}</p>
        </div>
        <div class="rounded-lg border bg-slate-50 p-3">
          <p class="text-xs uppercase text-slate-500">Owner claims</p>
          <p class="text-xl font-semibold">{{ claims.length }}</p>
        </div>
        <div class="rounded-lg border bg-slate-50 p-3">
          <p class="text-xs uppercase text-slate-500">Verification docs</p>
          <p class="text-xl font-semibold">{{ verificationDocs.length }}</p>
        </div>
      </div>
    </div>

    <div v-if="loading" class="rounded-lg border bg-white p-6 text-sm text-slate-600">Loading moderation queues...</div>
    <div v-else-if="errorMessage" class="rounded-lg border bg-white p-6 text-sm text-red-600">{{ errorMessage }}</div>

    <template v-else>
      <p v-if="actionFeedback" class="rounded-lg border bg-white p-3 text-sm text-slate-700">{{ actionFeedback }}</p>

      <section class="rounded-xl border bg-white p-5 shadow-sm">
        <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h2 class="text-lg font-semibold">Reports Queue</h2>
          <div class="flex gap-2">
            <select v-model="reportStatusFilter" class="rounded-md border px-2 py-1 text-xs">
              <option value="all">All statuses</option>
              <option value="open">Open</option>
              <option value="under_review">Under review</option>
              <option value="resolved">Resolved</option>
              <option value="rejected">Rejected</option>
            </select>
            <button class="rounded-md border px-3 py-1 text-xs hover:bg-slate-100" @click="loadQueues">Refresh</button>
          </div>
        </div>
        <div v-if="filteredReports.length === 0" class="text-sm text-slate-600">No reports in queue.</div>
        <div v-else class="space-y-3">
          <article v-for="report in filteredReports" :key="report.id" class="rounded-lg border p-3">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p class="font-medium">Report #{{ report.id }} · {{ report.report_type || 'unspecified' }}</p>
                <p class="text-xs text-slate-500">Restaurant: {{ report.restaurant_id || 'n/a' }}</p>
              </div>
              <span class="rounded-full border px-2 py-1 text-xs" :class="statusClass(report.status)">{{ report.status }}</span>
            </div>
            <p v-if="report.description" class="mt-2 text-sm text-slate-700">{{ report.description }}</p>
            <input v-model="reportNotes[report.id]" class="mt-2 w-full rounded border px-2 py-1 text-xs" placeholder="moderation note (optional)" />
            <div class="mt-2 flex gap-2">
              <button class="rounded border px-2 py-1 text-xs" @click="updateReportStatus(report, 'under_review')">Under review</button>
              <button class="rounded border px-2 py-1 text-xs" @click="updateReportStatus(report, 'resolved')">Resolve</button>
              <button class="rounded border px-2 py-1 text-xs" @click="updateReportStatus(report, 'rejected')">Reject</button>
            </div>
          </article>
        </div>
      </section>

      <section class="rounded-xl border bg-white p-5 shadow-sm">
        <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h2 class="text-lg font-semibold">Owner Claims Queue</h2>
          <div class="flex gap-2">
            <select v-model="claimStatusFilter" class="rounded-md border px-2 py-1 text-xs">
              <option value="all">All statuses</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>
            <button class="rounded-md border px-3 py-1 text-xs hover:bg-slate-100" @click="loadQueues">Refresh</button>
          </div>
        </div>
        <div v-if="filteredClaims.length === 0" class="text-sm text-slate-600">No owner claims in queue.</div>
        <div v-else class="space-y-3">
          <article v-for="claim in filteredClaims" :key="claim.id" class="rounded-lg border p-3">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p class="font-medium">Claim #{{ claim.id }} · Restaurant {{ claim.restaurant_id }}</p>
                <p class="text-xs text-slate-500">User: {{ claim.user_id }}</p>
              </div>
              <span class="rounded-full border px-2 py-1 text-xs" :class="statusClass(claim.status)">{{ claim.status }}</span>
            </div>
            <p v-if="claim.notes" class="mt-2 text-sm text-slate-700">Owner note: {{ claim.notes }}</p>
            <input v-model="claimNotes[claim.id]" class="mt-2 w-full rounded border px-2 py-1 text-xs" placeholder="moderation note (optional)" />
            <div class="mt-2 flex gap-2">
              <button class="rounded border px-2 py-1 text-xs" @click="updateClaimStatus(claim, 'approved')">Approve</button>
              <button class="rounded border px-2 py-1 text-xs" @click="updateClaimStatus(claim, 'rejected')">Reject</button>
            </div>
          </article>
        </div>
      </section>

      <section class="rounded-xl border bg-white p-5 shadow-sm">
        <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h2 class="text-lg font-semibold">Verification Documents Queue</h2>
          <div class="flex gap-2">
            <select v-model="verificationStatusFilter" class="rounded-md border px-2 py-1 text-xs">
              <option value="all">All statuses</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>
            <button class="rounded-md border px-3 py-1 text-xs hover:bg-slate-100" @click="loadQueues">Refresh</button>
          </div>
        </div>
        <div v-if="filteredVerificationDocs.length === 0" class="text-sm text-slate-600">No verification documents in queue.</div>
        <div v-else class="space-y-3">
          <article v-for="doc in filteredVerificationDocs" :key="doc.id" class="rounded-lg border p-3">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p class="font-medium">Document #{{ doc.id }} · claim {{ doc.owner_claim_id }} · {{ doc.document_type }}</p>
                <p class="text-xs text-slate-500">{{ doc.original_filename || 'metadata only' }}</p>
              </div>
              <span class="rounded-full border px-2 py-1 text-xs" :class="statusClass(doc.status)">{{ doc.status }}</span>
            </div>
            <input v-model="verificationNotes[doc.id]" class="mt-2 w-full rounded border px-2 py-1 text-xs" placeholder="moderation note (optional)" />
            <div class="mt-2 flex gap-2">
              <button class="rounded border px-2 py-1 text-xs" @click="updateVerificationStatus(doc, 'approved')">Approve</button>
              <button class="rounded border px-2 py-1 text-xs" @click="updateVerificationStatus(doc, 'rejected')">Reject</button>
            </div>
          </article>
        </div>
      </section>
    </template>
  </section>
</template>
