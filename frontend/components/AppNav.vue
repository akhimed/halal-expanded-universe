<script setup lang="ts">
const auth = useAuth()
auth.hydrate()

const onLogout = async () => {
  auth.logout()
  await navigateTo('/login')
}
</script>

<template>
  <header class="border-b bg-white/80 backdrop-blur">
    <nav class="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
      <NuxtLink to="/" class="text-lg font-semibold text-emerald-700">Faith + Dietary</NuxtLink>
      <div class="flex items-center gap-4 text-sm">
        <NuxtLink to="/search" class="text-slate-700 hover:text-emerald-700">Search</NuxtLink>
        <NuxtLink to="/favorites" class="text-slate-700 hover:text-emerald-700">Favorites</NuxtLink>
        <NuxtLink v-if="auth.isAuthenticated.value" to="/owner/dashboard" class="text-slate-700 hover:text-emerald-700">Owner</NuxtLink>
        <NuxtLink v-if="auth.isAuthenticated.value && (auth.user?.role === 'moderator' || auth.user?.role === 'admin')" to="/admin/dashboard" class="text-slate-700 hover:text-emerald-700">Admin</NuxtLink>
        <NuxtLink v-if="!auth.isAuthenticated.value" to="/login" class="text-slate-700 hover:text-emerald-700">Login</NuxtLink>
        <NuxtLink v-if="!auth.isAuthenticated.value" to="/register" class="text-slate-700 hover:text-emerald-700">Register</NuxtLink>
        <span v-if="auth.isAuthenticated.value" class="text-slate-500">{{ auth.user?.role }}</span>
        <button
          v-if="auth.isAuthenticated.value"
          class="rounded-md border px-2 py-1 text-xs text-slate-700 hover:bg-slate-100"
          @click="onLogout"
        >
          Logout
        </button>
      </div>
    </nav>
  </header>
</template>
