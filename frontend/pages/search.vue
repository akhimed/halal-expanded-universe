<script setup lang="ts">
import type { GroupParticipantInput, SearchProfile, SearchResult } from '~/types/api'

const api = useApiClient()
const auth = useAuth()
const favorites = useFavorites()

auth.hydrate()

const tagOptions = ['halal', 'kosher', 'hindu_vegetarian', 'vegan', 'vegetarian']
const allergenOptions = ['shellfish', 'nuts', 'dairy', 'gluten', 'soy', 'egg', 'sesame']
const profileOptions: SearchProfile[] = ['balanced', 'strict', 'community_first']

const locationPlaceholder = ref('Toronto, ON (coming soon)')
const selectedTags = ref<string[]>([])
const excludedAllergens = ref<string[]>([])
const profile = ref<SearchProfile>('balanced')
const loading = ref(false)
const errorMessage = ref('')
const results = ref<SearchResult[]>([])
const searched = ref(false)
const selectedRestaurantId = ref<number | null>(null)
const mobileShowMap = ref(false)

const groupMode = ref(false)
const participants = ref<GroupParticipantInput[]>([
  {
    participant_name: 'Participant 1',
    required_tags: [],
    excluded_allergens: [],
    profile: 'balanced'
  }
])

onMounted(async () => {
  if (auth.isAuthenticated.value) {
    await favorites.refreshFavorites()
  }
})

const addParticipant = () => {
  participants.value.push({
    participant_name: `Participant ${participants.value.length + 1}`,
    required_tags: [],
    excluded_allergens: [],
    profile: 'balanced'
  })
}

const removeParticipant = (index: number) => {
  if (participants.value.length <= 1) return
  participants.value.splice(index, 1)
}

const onSearch = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await api.searchRestaurants({
      required_tags: selectedTags.value,
      excluded_allergens: excludedAllergens.value,
      profile: profile.value,
      group_mode: groupMode.value,
      participants: groupMode.value ? participants.value : []
    })
    results.value = response.results
    searched.value = true
    selectedRestaurantId.value = response.results.length > 0 ? response.results[0].restaurant.id : null
  } catch (error) {
    errorMessage.value = api.humanizeError(error, 'Search failed.')
  } finally {
    loading.value = false
  }
}

const onSelectRestaurant = (restaurantId: number) => {
  selectedRestaurantId.value = restaurantId
}

const onToggleFavorite = async (restaurant: SearchResult['restaurant']) => {
  try {
    await favorites.toggleFavorite(restaurant)
  } catch {
    errorMessage.value = 'Please login to save favorites.'
  }
}
</script>

<template>
  <section class="space-y-6">
    <div class="grid grid-cols-1 gap-6 lg:grid-cols-4">
      <aside class="rounded-xl border bg-white p-4 shadow-sm lg:col-span-1">
        <h2 class="text-lg font-semibold">Search Filters</h2>

        <label class="mt-4 block text-sm font-medium">Location (placeholder)</label>
        <input
          v-model="locationPlaceholder"
          type="text"
          class="mt-1 w-full rounded-md border px-3 py-2 text-sm"
          placeholder="City or postal code"
        />

        <label class="mt-4 flex items-center gap-2 text-sm font-medium">
          <input v-model="groupMode" type="checkbox" class="rounded border" />
          Group mode
        </label>

        <template v-if="!groupMode">
          <label class="mt-4 block text-sm font-medium">Required Tags</label>
          <select v-model="selectedTags" multiple class="mt-1 h-32 w-full rounded-md border px-2 py-2 text-sm">
            <option v-for="tag in tagOptions" :key="tag" :value="tag">{{ tag }}</option>
          </select>

          <label class="mt-4 block text-sm font-medium">Excluded Allergens</label>
          <select
            v-model="excludedAllergens"
            multiple
            class="mt-1 h-32 w-full rounded-md border px-2 py-2 text-sm"
          >
            <option v-for="allergen in allergenOptions" :key="allergen" :value="allergen">
              {{ allergen }}
            </option>
          </select>

          <label class="mt-4 block text-sm font-medium">Profile</label>
          <select v-model="profile" class="mt-1 w-full rounded-md border px-3 py-2 text-sm">
            <option v-for="item in profileOptions" :key="item" :value="item">{{ item }}</option>
          </select>
        </template>

        <template v-else>
          <div class="mt-4 space-y-3">
            <div v-for="(participant, index) in participants" :key="index" class="rounded-md border bg-slate-50 p-3">
              <div class="flex items-center justify-between gap-2">
                <input v-model="participant.participant_name" class="w-full rounded border px-2 py-1 text-sm" />
                <button
                  class="rounded border px-2 py-1 text-xs hover:bg-slate-100"
                  :disabled="participants.length <= 1"
                  @click="removeParticipant(index)"
                >
                  Remove
                </button>
              </div>

              <label class="mt-2 block text-xs font-medium">Required Tags</label>
              <select v-model="participant.required_tags" multiple class="mt-1 h-20 w-full rounded border px-2 py-1 text-xs">
                <option v-for="tag in tagOptions" :key="tag" :value="tag">{{ tag }}</option>
              </select>

              <label class="mt-2 block text-xs font-medium">Excluded Allergens</label>
              <select
                v-model="participant.excluded_allergens"
                multiple
                class="mt-1 h-20 w-full rounded border px-2 py-1 text-xs"
              >
                <option v-for="allergen in allergenOptions" :key="allergen" :value="allergen">{{ allergen }}</option>
              </select>

              <label class="mt-2 block text-xs font-medium">Profile</label>
              <select v-model="participant.profile" class="mt-1 w-full rounded border px-2 py-1 text-xs">
                <option v-for="item in profileOptions" :key="item" :value="item">{{ item }}</option>
              </select>
            </div>

            <button class="w-full rounded-md border px-3 py-1 text-xs hover:bg-slate-100" @click="addParticipant">
              Add participant
            </button>
          </div>
        </template>

        <button
          class="mt-5 w-full rounded-md bg-emerald-600 px-4 py-2 text-white hover:bg-emerald-700 disabled:opacity-60"
          :disabled="loading"
          @click="onSearch"
        >
          {{ loading ? 'Searching...' : 'Search' }}
        </button>

        <p v-if="errorMessage" class="mt-3 text-sm text-red-600">{{ errorMessage }}</p>
      </aside>

      <div class="space-y-4 lg:col-span-3">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-semibold">Results</h2>
          <button
            class="rounded-md border bg-white px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-100 lg:hidden"
            @click="mobileShowMap = !mobileShowMap"
          >
            {{ mobileShowMap ? 'Show List' : 'Show Map' }}
          </button>
        </div>

        <div v-if="loading" class="rounded-lg border bg-white p-6 text-sm text-slate-600">Loading results...</div>

        <div
          v-else-if="searched && results.length === 0"
          class="rounded-lg border bg-white p-6 text-sm text-slate-600"
        >
          No restaurants matched your filters.
        </div>

        <div v-else-if="!searched" class="rounded-lg border bg-white p-6 text-sm text-slate-600">
          Choose filters and click Search.
        </div>

        <div v-else class="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <div class="space-y-3" :class="mobileShowMap ? 'hidden lg:block' : ''">
            <ResultCard
              v-for="result in results"
              :key="result.restaurant.id"
              :result="result"
              :selected="selectedRestaurantId === result.restaurant.id"
              :is-favorited="favorites.isFavorited(result.restaurant.id)"
              @select="onSelectRestaurant"
              @toggle-favorite="onToggleFavorite"
            />
          </div>

          <ClientOnly>
            <div class="xl:sticky xl:top-6" :class="!mobileShowMap ? 'hidden lg:block' : ''">
              <SearchResultsMap
                :results="results"
                :selected-restaurant-id="selectedRestaurantId"
                @select="onSelectRestaurant"
              />
            </div>
          </ClientOnly>
        </div>
      </div>
    </div>
  </section>
</template>
