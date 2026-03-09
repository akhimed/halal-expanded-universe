<template>
  <main style="font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto;">
    <h1>Faith + Dietary Discovery</h1>
    <p>Production UI scaffold (Nuxt 3). Backend is expected at {{ apiBaseUrl }}.</p>

    <div style="margin: 16px 0;">
      <button @click="pingHealth">Check Backend Health</button>
    </div>

    <pre v-if="healthResponse">{{ healthResponse }}</pre>
  </main>
</template>

<script setup lang="ts">
const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl as string
const healthResponse = ref('')

const pingHealth = async () => {
  try {
    const data = await $fetch(`${apiBaseUrl}/health`)
    healthResponse.value = JSON.stringify(data, null, 2)
  } catch (error) {
    healthResponse.value = String(error)
  }
}
</script>
