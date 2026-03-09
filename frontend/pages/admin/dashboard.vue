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

const isModerator = computed(() => auth.user.value?.role === 'moderator' || auth.user.value?.role === 'admin')

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
    const updated = await api.updateModerationReport(report.id, { status })
    const target = reports.value.find((r) => r.id === report.id)
    if (target) target.status = updated.status
    actionFeedback.value = `Report #${report.id} updated to ${status}.`
  } catch (error) {
    actionFeedback.value = api.humanizeError(error, 'Failed to update report.')
  }
}

const updateClaimStatus = async (claim: ModerationOwnerClaimItem, status: 'approved' | 'rejected') => {
  try {
    const updated = await api.updateModerationOwnerClaim(claim.id, { status })
    const target = claims.value.find((c) => c.id === claim.id)
    if (target) target.status = updated.status
    actionFeedback.value = `Claim #${claim.id} updated to ${status}.`
  } catch (error) {
    actionFeedback.value = api.humanizeError(error, 'Failed to update claim.')
  }
}

const updateVerificationStatus = async (doc: VerificationDocument, status: 'approved' | 'rejected') => {
  try {
    const updated = await api.updateModerationVerificationDocument(doc.id, { status })
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
    </div>

    <div v-if="loading" class="rounded-lg border bg-white p-6 text-sm text-slate-600">Loading moderation queues...</div>
    <div v-else-if="errorMessage" class="rounded-lg border bg-white p-6 text-sm text-red-600">{{ errorMessage }}</div>

    <template v-else>
      <p v-if="actionFeedback" class="rounded-lg border bg-white p-3 text-sm text-slate-700">{{ actionFeedback }}</p>

      <section class="rounded-xl border bg-white p-5 shadow-sm">
        <div class="mb-3 flex items-center justify-between">
          <h2 class="text-lg font-semibold">Reports Queue</h2>
          <button class="rounded-md border px-3 py-1 text-xs hover:bg-slate-100" @click="loadQueues">Refresh</button>
        </div>
        <div v-if="reports.length === 0" class="text-sm text-slate-600">No reports in queue.</div>
        <div v-else class="space-y-3">
          <article v-for="report in reports" :key="report.id" class="rounded-lg border p-3">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p class="font-medium">Report #{{ report.id }} · {{ report.report_type || 'unspecified' }}</p>
                <p class="text-xs text-slate-500">Restaurant: {{ report.restaurant_id || 'n/a' }} · Status: {{ report.status }}</p>
              </div>
              <div class="flex gap-2">
                <button class="rounded border px-2 py-1 text-xs" @click="updateReportStatus(report, 'under_review')">Under review</button>
                <button class="rounded border px-2 py-1 text-xs" @click="updateReportStatus(report, 'resolved')">Resolve</button>
                <button class="rounded border px-2 py-1 text-xs" @click="updateReportStatus(report, 'rejected')">Reject</button>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section class="rounded-xl border bg-white p-5 shadow-sm">
        <div class="mb-3 flex items-center justify-between">
          <h2 class="text-lg font-semibold">Owner Claims Queue</h2>
          <button class="rounded-md border px-3 py-1 text-xs hover:bg-slate-100" @click="loadQueues">Refresh</button>
        </div>
        <div v-if="claims.length === 0" class="text-sm text-slate-600">No owner claims in queue.</div>
        <div v-else class="space-y-3">
          <article v-for="claim in claims" :key="claim.id" class="rounded-lg border p-3">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p class="font-medium">Claim #{{ claim.id }} · Restaurant {{ claim.restaurant_id }}</p>
                <p class="text-xs text-slate-500">User: {{ claim.user_id }} · Status: {{ claim.status }}</p>
              </div>
              <div class="flex gap-2">
                <button class="rounded border px-2 py-1 text-xs" @click="updateClaimStatus(claim, 'approved')">Approve</button>
                <button class="rounded border px-2 py-1 text-xs" @click="updateClaimStatus(claim, 'rejected')">Reject</button>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section class="rounded-xl border bg-white p-5 shadow-sm">
        <div class="mb-3 flex items-center justify-between">
          <h2 class="text-lg font-semibold">Verification Documents Queue</h2>
          <button class="rounded-md border px-3 py-1 text-xs hover:bg-slate-100" @click="loadQueues">Refresh</button>
        </div>
        <div v-if="verificationDocs.length === 0" class="text-sm text-slate-600">No verification documents in queue.</div>
        <div v-else class="space-y-3">
          <article v-for="doc in verificationDocs" :key="doc.id" class="rounded-lg border p-3">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p class="font-medium">Document #{{ doc.id }} · claim {{ doc.owner_claim_id }} · {{ doc.document_type }}</p>
                <p class="text-xs text-slate-500">Status: {{ doc.status }} · {{ doc.original_filename || 'metadata only' }}</p>
              </div>
              <div class="flex gap-2">
                <button class="rounded border px-2 py-1 text-xs" @click="updateVerificationStatus(doc, 'approved')">Approve</button>
                <button class="rounded border px-2 py-1 text-xs" @click="updateVerificationStatus(doc, 'rejected')">Reject</button>
              </div>
            </div>
          </article>
        </div>
      </section>
    </template>
  </section>
</template>
