import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { comparisonKeys, loadComparisons, addToComparison, removeFromComparison } from '@/lib/queries'

export default function useComparison(options: { kind: number }) {
  const queryClient = useQueryClient()

  const { kind } = options || { kind: null } // we use null instead of undefined to comply with SSR props in '/compare'

  const { data: comparisons, isSuccess, isLoading, isError } = useQuery({
    queryKey: comparisonKeys.list(kind),
    queryFn: () => loadComparisons(kind),
    initialData: [],
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
