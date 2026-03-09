<script setup lang="ts">
const props = defineProps<{
  latitude: number | null
  longitude: number | null
  name: string
}>()

const mapRoot = ref<HTMLElement | null>(null)
let map: any = null
let maplibre: any = null

onMounted(async () => {
  if (!mapRoot.value || props.latitude === null || props.longitude === null) {
    return
  }

  maplibre = await import('maplibre-gl')
  map = new maplibre.Map({
    container: mapRoot.value,
    style: 'https://demotiles.maplibre.org/style.json',
    center: [props.longitude, props.latitude],
    zoom: 13
  })

  map.addControl(new maplibre.NavigationControl(), 'top-right')
  new maplibre.Marker().setLngLat([props.longitude, props.latitude]).addTo(map)
})

onBeforeUnmount(() => {
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<template>
  <div class="h-72 w-full overflow-hidden rounded-xl border bg-white">
    <div v-if="latitude === null || longitude === null" class="flex h-full items-center justify-center px-4 text-sm text-slate-500">
      Location coordinates are not available for this restaurant.
    </div>
    <div v-else ref="mapRoot" class="h-full w-full" />
  </div>
</template>
