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
  props.selectedRestaurantId === restaurantId ? 'bg-emerald-600 scale-125' : 'bg-slate-700'

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

    const popup = new maplibre.Popup({ offset: 18 }).setHTML(`\n      <div class="text-xs">\n        <p class="font-semibold">${item.restaurant.name}</p>\n        <p class="text-slate-500">Trust ${item.trust_score}/100</p>\n      </div>\n    `)

    const marker = new maplibre.Marker({ element: el })
      .setLngLat([item.restaurant.longitude, item.restaurant.latitude])
      .setPopup(popup)
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
  (selectedRestaurantId) => {
    renderMarkers()
    if (!map || !selectedRestaurantId) return
    const selected = resultsWithCoords.value.find((item) => item.restaurant.id === selectedRestaurantId)
    if (!selected) return
    map.flyTo({
      center: [selected.restaurant.longitude, selected.restaurant.latitude],
      zoom: Math.max(map.getZoom(), 12),
      essential: true
    })
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
  <div class="h-[420px] w-full overflow-hidden rounded-xl border bg-white shadow-sm">
    <div v-if="resultsWithCoords.length === 0" class="flex h-full items-center justify-center px-4 text-sm text-slate-500">
      No mappable coordinates in current results.
    </div>
    <div v-else ref="mapRoot" class="h-full w-full" />
  </div>
</template>
