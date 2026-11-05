import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { comparisonKeys, loadComparisons, addToComparison, removeFromComparison } from '@/lib/queries'

const noComparisons: number[] = []

export default function useComparison(options?: { kind: number | null }) {
  const queryClient = useQueryClient()

  const { kind } = options || { kind: null } // null like a missing kind in the '/compare' query

  // Initial data would count as fresh under the App Router's default staleTime and skip the first request,
  // so the list is empty until it is loaded and isSuccess tells that it is
  const { data: comparisons = noComparisons, isSuccess, isLoading, isError } = useQuery({
    queryKey: comparisonKeys.list(kind),
    queryFn: () => loadComparisons(kind),
  })

  const addToComparisonMutation = useMutation({
    mutationFn: (productId: number) => addToComparison(productId),
    onSuccess: (data) => {
      queryClient.setQueryData(comparisonKeys.list(null), data)
    }
  })
  const removeFromComparisonMutation = useMutation({
    mutationFn: (productId: number) => removeFromComparison(productId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: comparisonKeys.lists() })
      queryClient.setQueryData(comparisonKeys.list(null), data)
    }
  })

  const compare = (productId: number) => {
    addToComparisonMutation.mutate(productId)
  }

  const uncompare = (productId: number, callback: (data: number[]) => void) => {
    removeFromComparisonMutation.mutate(productId, {
      onSuccess: (data) => {
        if (callback !== undefined)
          callback(data)
      }
    })
  }

  return { comparisons, compare, uncompare, isSuccess, isLoading, isError }
}
