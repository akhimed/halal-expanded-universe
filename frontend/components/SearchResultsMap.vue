<script setup lang="ts">
import type { SearchResult } from '~/types/api'

const props = defineProps<{
  results: SearchResult[]
  selectedRestaurantId: number | null
}>()

const emit = defineEmits<{
  select: [restaurantId: number]
}>()

const mapRoot = ref<HTMLElement | null>(null)
let map: any = null
let maplibre: any = null
let markers: any[] = []

const resultsWithCoords = computed(() =>
  props.results.filter((item) => item.restaurant.latitude !== null && item.restaurant.longitude !== null)
)

const clearMarkers = () => {
  markers.forEach((marker) => marker.remove())
  markers = []
}

const markerColor = (restaurantId: number) =>
  props.selectedRestaurantId === restaurantId ? 'bg-emerald-600' : 'bg-slate-700'

const renderMarkers = () => {
  if (!map || !maplibre) {
    return
  }

  clearMarkers()

  for (const item of resultsWithCoords.value) {
    const el = document.createElement('button')
    el.className = `h-4 w-4 rounded-full border-2 border-white shadow ${markerColor(item.restaurant.id)}`
    el.title = item.restaurant.name
    el.addEventListener('click', () => emit('select', item.restaurant.id))

    const marker = new maplibre.Marker({ element: el })
      .setLngLat([item.restaurant.longitude, item.restaurant.latitude])
      .addTo(map)

    markers.push(marker)
  }
}

const fitMapToResults = () => {
  if (!map || resultsWithCoords.value.length === 0) {
    return
  }

  if (resultsWithCoords.value.length === 1) {
    const only = resultsWithCoords.value[0]
    map.flyTo({ center: [only.restaurant.longitude, only.restaurant.latitude], zoom: 12 })
    return
  }

  const bounds = new maplibre.LngLatBounds()
  for (const item of resultsWithCoords.value) {
    bounds.extend([item.restaurant.longitude, item.restaurant.latitude])
  }
  map.fitBounds(bounds, { padding: 40 })
}

onMounted(async () => {
  if (!mapRoot.value) {
    return
  }

  maplibre = await import('maplibre-gl')
  map = new maplibre.Map({
    container: mapRoot.value,
    style: 'https://demotiles.maplibre.org/style.json',
    center: [-79.3832, 43.6532],
    zoom: 10
  })

  map.addControl(new maplibre.NavigationControl(), 'top-right')
  map.on('load', () => {
    renderMarkers()
    fitMapToResults()
  })
})

watch(
  () => props.results,
  () => {
    renderMarkers()
    fitMapToResults()
  },
  { deep: true }
)

watch(
  () => props.selectedRestaurantId,
  () => {
    renderMarkers()
  }
)

onBeforeUnmount(() => {
  clearMarkers()
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<template>
  <div class="h-[420px] w-full overflow-hidden rounded-xl border bg-white">
    <div v-if="resultsWithCoords.length === 0" class="flex h-full items-center justify-center px-4 text-sm text-slate-500">
      No mappable coordinates in current results.
    </div>
    <div v-else ref="mapRoot" class="h-full w-full" />
  </div>
</template>
