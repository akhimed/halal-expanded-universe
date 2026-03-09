<script setup lang="ts">
const api = useApiClient()
const auth = useAuth()

auth.hydrate()
if (auth.isAuthenticated.value) {
  await navigateTo('/favorites')
}

const email = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

const onLogin = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await api.login({ email: email.value, password: password.value })
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
    <h1 class="text-2xl font-bold">Login</h1>
    <p class="mt-1 text-sm text-slate-600">Sign in with your email and password.</p>

    <label class="mt-4 block text-sm font-medium">Email</label>
    <input v-model="email" type="email" class="mt-1 w-full rounded-md border px-3 py-2 text-sm" />

    <label class="mt-4 block text-sm font-medium">Password</label>
    <input v-model="password" type="password" class="mt-1 w-full rounded-md border px-3 py-2 text-sm" />

    <button
      class="mt-5 w-full rounded-md bg-emerald-600 px-4 py-2 text-white hover:bg-emerald-700 disabled:opacity-60"
      :disabled="loading"
      @click="onLogin"
    >
      {{ loading ? 'Signing in...' : 'Login' }}
    </button>

    <p v-if="errorMessage" class="mt-3 text-sm text-red-600">{{ errorMessage }}</p>
    <p class="mt-4 text-sm text-slate-600">No account? <NuxtLink to="/register" class="text-emerald-700">Register</NuxtLink></p>
  </section>
</template>
