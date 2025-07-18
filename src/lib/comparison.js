import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { comparisonKeys, loadComparisons, addToComparison, removeFromComparison } from '@/lib/queries';

export default function useComparison(options) {
    const queryClient = useQueryClient();

    const { kind } = options || { kind: null }; // we use null instead of undefined to comply with SSR props in '/compare'

    const { data: comparisons, isSuccess, isLoading, isError } = useQuery({
        queryKey: comparisonKeys.list(kind),
        queryFn: () => loadComparisons(kind),
        initialData: [],
    });

    const addToComparisonMutation = useMutation({
        mutationFn: (productId) => addToComparison(productId),
        onSuccess: (data) => {
            queryClient.setQueryData(comparisonKeys.list(null), data);
        }
    });
    const removeFromComparisonMutation = useMutation({
        mutationFn: (productId) => removeFromComparison(productId),
        onSuccess: (data) => {
            queryClient.invalidateQueries({queryKey: comparisonKeys.lists()});
            queryClient.setQueryData(comparisonKeys.list(null), data);
        }
    });

    const compare = (productId) => {
        addToComparisonMutation.mutate(productId);
    };

    const uncompare = (productId, callback) => {
        removeFromComparisonMutation.mutate(productId, {
            onSuccess: (data) => {
                if (callback !== undefined)
                    callback(data);
            }
        });
    };

    return { comparisons, compare, uncompare, isSuccess, isLoading, isError };
}
