<script setup lang="ts">
definePageMeta({
  middleware: ['auth'],
  requiresAuth: true
})

const auth = useAuth()
const favorites = useFavorites()

auth.hydrate()

onMounted(async () => {
  await favorites.refreshFavorites()
})

const onRemove = async (restaurantId: number) => {
  const target = favorites.favoriteRestaurants.value.find((item) => item.id === restaurantId)
  if (!target) return
  await favorites.toggleFavorite(target)
}
</script>

<template>
  <section class="space-y-4">
    <div class="rounded-xl border bg-white p-6 shadow-sm">
      <h1 class="text-2xl font-bold">Favorites</h1>
      <p class="mt-2 text-slate-600">Saved places for {{ auth.user?.display_name }}.</p>
      <p class="mt-1 text-sm text-slate-500">Role: {{ auth.user?.role }}</p>
    </div>

    <div v-if="favorites.loadingFavorites" class="rounded-lg border bg-white p-6 text-sm text-slate-600">
      Loading favorites...
    </div>

    <div v-else-if="favorites.favoriteRestaurants.length === 0" class="rounded-lg border bg-white p-6 text-sm text-slate-600">
      No saved places yet.
    </div>

    <div v-else class="grid grid-cols-1 gap-4 md:grid-cols-2">
      <article v-for="item in favorites.favoriteRestaurants" :key="item.id" class="rounded-lg border bg-white p-4 shadow-sm">
        <NuxtLink :to="`/restaurants/${item.id}`" class="text-lg font-semibold text-emerald-700 hover:underline">
          {{ item.name }}
        </NuxtLink>
        <p class="mt-1 text-sm text-slate-600">{{ item.address || 'Address unavailable' }}</p>
        <button class="mt-3 rounded-md border px-3 py-1 text-xs text-slate-700 hover:bg-slate-100" @click="onRemove(item.id)">
          Remove
        </button>
      </article>
    </div>
  </section>
</template>
