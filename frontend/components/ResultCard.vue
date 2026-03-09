<script setup lang="ts">
import type { SearchResult } from '~/types/api'

const props = defineProps<{
  result: SearchResult
  selected?: boolean
  isFavorited?: boolean
}>()

const emit = defineEmits<{
  select: [restaurantId: number]
  toggleFavorite: [restaurant: SearchResult['restaurant']]
}>()
</script>

<template>
  <article
    class="rounded-lg border bg-white p-4 shadow-sm transition"
    :class="selected ? 'border-emerald-500 ring-2 ring-emerald-200' : 'border-slate-200'"
    @click="emit('select', result.restaurant.id)"
  >
    <div class="flex items-start justify-between gap-3">
      <div>
        <NuxtLink
          :to="`/restaurants/${result.restaurant.id}`"
          class="text-lg font-semibold text-emerald-700 hover:underline"
          @click.stop
        >
          {{ result.restaurant.name }}
        </NuxtLink>
        <p class="mt-1 text-sm text-slate-600">{{ result.restaurant.address || 'Address unavailable' }}</p>
      </div>
      <div class="flex flex-col items-end gap-2">
        <span class="rounded-full bg-emerald-100 px-3 py-1 text-sm font-medium text-emerald-800">
          Trust {{ result.trust_score }}
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

    <div class="mt-3 flex flex-wrap gap-2">
      <span
        v-for="tag in result.matched_tags"
        :key="tag"
        class="rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-700"
      >
        {{ tag }}
      </span>
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
