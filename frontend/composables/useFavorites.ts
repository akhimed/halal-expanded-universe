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

  const addFavorite = async (restaurantId: number) => {
    if (!auth.isAuthenticated.value) {
      throw new Error('Login required to save favorites')
    }
    await api.saveFavorite(restaurantId)
    await refreshFavorites()
  }

  const removeFavorite = async (restaurantId: number) => {
    if (!auth.isAuthenticated.value) {
      throw new Error('Login required to manage favorites')
    }
    await api.removeFavorite(restaurantId)
    favoriteRestaurants.value = favoriteRestaurants.value.filter((item) => item.id !== restaurantId)
  }

  const toggleFavorite = async (restaurant: RestaurantSummary) => {
    if (!auth.isAuthenticated.value) {
      throw new Error('Login required to save favorites')
    }

    if (isFavorited(restaurant.id)) {
      await removeFavorite(restaurant.id)
    } else {
      await addFavorite(restaurant.id)
    }
  }

  return {
    favoriteRestaurants,
    loadingFavorites,
    favoriteIds,
    refreshFavorites,
    addFavorite,
    removeFavorite,
    isFavorited,
    toggleFavorite
  }
}
