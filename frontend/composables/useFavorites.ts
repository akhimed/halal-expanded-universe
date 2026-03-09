import type { RestaurantSummary } from '~/types/api'

export const useFavorites = () => {
  const api = useApiClient()
  const auth = useAuth()

  const favoriteRestaurants = useState<RestaurantSummary[]>('favorite_restaurants', () => [])
  const loadingFavorites = useState<boolean>('favorite_loading', () => false)

  const favoriteIds = computed(() => new Set(favoriteRestaurants.value.map((item) => item.id)))

  const refreshFavorites = async () => {
    if (!auth.isAuthenticated.value) {
      favoriteRestaurants.value = []
      return
    }
    loadingFavorites.value = true
    try {
      const response = await api.listFavorites()
      favoriteRestaurants.value = response.favorites
    } finally {
      loadingFavorites.value = false
    }
  }

  const isFavorited = (restaurantId: number) => favoriteIds.value.has(restaurantId)

  const toggleFavorite = async (restaurant: RestaurantSummary) => {
    if (!auth.isAuthenticated.value) {
      throw new Error('Login required to save favorites')
    }

    if (isFavorited(restaurant.id)) {
      await api.removeFavorite(restaurant.id)
    } else {
      await api.saveFavorite(restaurant.id)
    }

    await refreshFavorites()
  }

  return {
    favoriteRestaurants,
    loadingFavorites,
    favoriteIds,
    refreshFavorites,
    isFavorited,
    toggleFavorite
  }
}
