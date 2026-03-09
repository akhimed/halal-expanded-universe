<script setup lang="ts">
const api = useApiClient()
const auth = useAuth()

const displayName = ref('')
const email = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

const onRegister = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await api.register({
      display_name: displayName.value,
      email: email.value,
      password: password.value
    })
    auth.setSession(response)
    await navigateTo('/favorites')
  } catch (error) {
    errorMessage.value = String(error)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="mx-auto max-w-md rounded-xl border bg-white p-6 shadow-sm">
    <h1 class="text-2xl font-bold">Register</h1>
    <p class="mt-1 text-sm text-slate-600">Create an account (default role: user).</p>

    <label class="mt-4 block text-sm font-medium">Display Name</label>
    <input v-model="displayName" type="text" class="mt-1 w-full rounded-md border px-3 py-2 text-sm" />

    <label class="mt-4 block text-sm font-medium">Email</label>
    <input v-model="email" type="email" class="mt-1 w-full rounded-md border px-3 py-2 text-sm" />

    <label class="mt-4 block text-sm font-medium">Password</label>
    <input v-model="password" type="password" class="mt-1 w-full rounded-md border px-3 py-2 text-sm" />

    <button
      class="mt-5 w-full rounded-md bg-emerald-600 px-4 py-2 text-white hover:bg-emerald-700 disabled:opacity-60"
      :disabled="loading"
      @click="onRegister"
    >
      {{ loading ? 'Creating account...' : 'Register' }}
    </button>

    <p v-if="errorMessage" class="mt-3 text-sm text-red-600">{{ errorMessage }}</p>
    <p class="mt-4 text-sm text-slate-600">Already have an account? <NuxtLink to="/login" class="text-emerald-700">Login</NuxtLink></p>
  </section>
</template>
