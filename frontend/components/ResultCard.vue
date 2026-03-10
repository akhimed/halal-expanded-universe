<script setup lang="ts">
import type { SearchResult } from '~/types/api'
import { formatDistanceKm } from '~/utils/location'

const props = defineProps<{
  result: SearchResult
  selected?: boolean
  isFavorited?: boolean
}>()

const emit = defineEmits<{
  select: [restaurantId: number]
  toggleFavorite: [restaurant: SearchResult['restaurant']]
}>()

const trustBadgeClass = computed(() => {
  if (props.result.trust_level === 'high') return 'bg-emerald-100 text-emerald-800'
  if (props.result.trust_level === 'medium') return 'bg-amber-100 text-amber-800'
  return 'bg-rose-100 text-rose-800'
})
</script>

<template>
  <article
    class="cursor-pointer rounded-lg border bg-white p-4 shadow-sm transition hover:border-emerald-300"
    :class="selected ? 'border-emerald-500 ring-2 ring-emerald-200' : 'border-slate-200'"
    @click="emit('select', result.restaurant.id)"
  >
    <div class="flex items-start justify-between gap-3">
      <div>
        <NuxtLink
          :to="{ path: `/restaurants/${result.restaurant.id}`, query: { explanation: result.full_explanation, distance_km: result.distance_km } }"
          class="text-lg font-semibold text-emerald-700 hover:underline"
          @click.stop
        >
          {{ result.restaurant.name }}
        </NuxtLink>
        <p class="mt-1 text-sm text-slate-600">{{ result.restaurant.address || 'Address unavailable' }}</p>
        <p v-if="distanceLabel" class="text-xs text-slate-500">{{ distanceLabel }} away</p>
      </div>
      <div class="flex flex-col items-end gap-2">
        <span class="rounded-full px-3 py-1 text-sm font-medium" :class="trustBadgeClass">
          Trust {{ result.trust_score }}/100 · {{ result.trust_level }}
        </span>
        <button
          class="rounded-md border px-2 py-1 text-xs"
          :class="isFavorited ? 'border-amber-300 bg-amber-50 text-amber-700' : 'text-slate-700 hover:bg-slate-100'"
          @click.stop="emit('toggleFavorite', result.restaurant)"
        >
          {{ isFavorited ? 'Saved' : 'Save' }}
        </button>
      </div>
    </div>



    <div v-if="result.trust_caveats.length > 0" class="mt-3 rounded-md border border-rose-200 bg-rose-50 p-2 text-xs text-rose-800">
      <p class="font-medium">Trust caveats</p>
      <ul class="mt-1 list-disc pl-4">
        <li v-for="caveat in result.trust_caveats" :key="caveat">{{ caveat }}</li>
      </ul>
    </div>

    <div class="mt-3 flex flex-wrap gap-2">
      <span
        v-for="tag in result.matched_tags"
        :key="tag"
        class="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700"
      >
        {{ tag }}
      </span>
      <span v-if="result.matched_tags.length === 0" class="text-xs text-slate-500">No required tags matched.</span>
    </div>


    <div class="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
      <div class="rounded-md bg-slate-50 p-2">
        <p class="text-slate-500">Match tags</p>
        <p class="font-semibold text-slate-800">{{ result.matched_tags.length }}</p>
      </div>
      <div class="rounded-md bg-slate-50 p-2">
        <p class="text-slate-500">Allergen checks</p>
        <p class="font-semibold text-slate-800">{{ result.excluded_allergen_status.length }}</p>
      </div>
      <div class="rounded-md bg-slate-50 p-2">
        <p class="text-slate-500">Group fit</p>
        <p class="font-semibold text-slate-800">
          {{ result.group_fit_score !== null && result.group_fit_score !== undefined ? result.group_fit_score : '—' }}
        </p>
      </div>
    </div>

    <div v-if="result.excluded_allergen_status.length > 0" class="mt-3 rounded-md border border-slate-200 p-2 text-xs">
      <p class="font-medium text-slate-700">Allergen compatibility</p>
      <ul class="mt-1 space-y-1 text-slate-600">
        <li v-for="item in result.excluded_allergen_status" :key="item.allergen">
          {{ item.allergen }}: {{ item.present ? 'present (conflict)' : 'not present' }}
        </li>
      </ul>
    </div>


    <div v-if="result.group_fit_score !== null && result.group_fit_score !== undefined" class="mt-3 rounded-md bg-indigo-50 p-2 text-xs text-indigo-800">
      Group fit: {{ result.group_fit_score }}
    </div>

    <div v-if="result.participant_satisfaction.length > 0" class="mt-3 space-y-2">
      <div
        v-for="participant in result.participant_satisfaction"
        :key="participant.participant_name"
        class="rounded-md border bg-slate-50 p-2 text-xs"
      >
        <p class="font-medium">{{ participant.participant_name }} ({{ participant.profile }})</p>
        <p>Required tags: {{ participant.required_tags_satisfied ? 'satisfied' : `missing: ${participant.missing_required_tags.join(', ') || 'none'}` }}</p>
        <p>Allergens: {{ participant.excluded_allergens_satisfied ? 'safe' : `conflicts: ${participant.conflicting_allergens.join(', ')}` }}</p>
      </div>
    </div>

    <p class="mt-3 text-sm text-slate-700 line-clamp-3">{{ result.explanation }}</p>
  </article>
</template>
