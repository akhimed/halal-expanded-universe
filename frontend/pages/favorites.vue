<script setup lang="ts">
definePageMeta({
  middleware: ['auth'],
  requiresAuth: true
})

const auth = useAuth()
const favorites = useFavorites()
const isRemoving = ref<number | null>(null)
const errorMessage = ref('')

auth.hydrate()

onMounted(async () => {
  errorMessage.value = ''
  try {
    await favorites.refreshFavorites()
  } catch (error) {
    errorMessage.value = String(error)
  }
})

const onRemove = async (restaurantId: number) => {
  isRemoving.value = restaurantId
  errorMessage.value = ''
  try {
    await favorites.removeFavorite(restaurantId)
  } catch (error) {
    errorMessage.value = String(error)
  } finally {
    isRemoving.value = null
  }
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

    <div v-if="errorMessage" class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
      {{ errorMessage }}
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
        <button
          class="mt-3 rounded-md border px-3 py-1 text-xs text-slate-700 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="isRemoving === item.id"
          @click="onRemove(item.id)"
        >
          {{ isRemoving === item.id ? 'Removing...' : 'Remove' }}
        </button>
      </article>
    </div>
  </section>
</template>
