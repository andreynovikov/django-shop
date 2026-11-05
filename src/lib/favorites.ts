import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { useSession } from '@/lib/session'
import { favoriteKeys, loadFavorites, addToFavorites, removeFromFavorites } from '@/lib/queries'

const noFavorites: number[] = []

export default function useFavorites() {
  const { status } = useSession()

  const queryClient = useQueryClient()

  // Initial data would count as fresh under the App Router's default staleTime and skip the first request,
  // so the list is empty until it is loaded and isSuccess tells that it is
  const { data: favorites = noFavorites, isSuccess, isLoading, isError } = useQuery({
    queryKey: favoriteKeys.details(),
    queryFn: () => loadFavorites(),
    enabled: status === 'authenticated',
  })

  const addToFavoritesMutation = useMutation({
    mutationFn: (productId: number) => addToFavorites(productId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: favoriteKeys.all })
    }
  })
  const removeFromFavoritesMutation = useMutation({
    mutationFn: (productId: number) => removeFromFavorites(productId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: favoriteKeys.all })
    }
  })

  const favoritize = (productId: number) => {
    addToFavoritesMutation.mutate(productId)
  }

  const unfavoritize = (productId: number) => {
    removeFromFavoritesMutation.mutate(productId)
  }

  return { favorites, favoritize, unfavoritize, isSuccess, isLoading, isError }
}
