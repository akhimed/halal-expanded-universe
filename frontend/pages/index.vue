<script setup lang="ts">
const api = useApiClient()
const loading = ref(false)
const healthData = ref<string>('')

const checkHealth = async () => {
  loading.value = true
  healthData.value = ''
  try {
    const response = await api.getHealth()
    healthData.value = JSON.stringify(response, null, 2)
  } catch (error) {
    healthData.value = String(error)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="space-y-6">
    <div class="rounded-xl border bg-white p-6 shadow-sm">
      <h1 class="text-2xl font-bold">Faith + Dietary Discovery</h1>
      <p class="mt-2 text-slate-600">
        Find restaurants by halal, kosher, hindu_vegetarian, vegan, vegetarian and allergen-safe needs.
      </p>
      <div class="mt-4 flex gap-3">
        <NuxtLink to="/search" class="rounded-md bg-emerald-600 px-4 py-2 text-white hover:bg-emerald-700">
          Start Search
        </NuxtLink>
        <button
          class="rounded-md border px-4 py-2 text-slate-700 hover:bg-slate-100"
          :disabled="loading"
          @click="checkHealth"
        >
          {{ loading ? 'Checking...' : 'Check Backend Health' }}
        </button>
      </div>
      <pre v-if="healthData" class="mt-4 overflow-x-auto rounded-md bg-slate-900 p-3 text-xs text-slate-100">{{ healthData }}</pre>
    </div>
  </section>
</template>
