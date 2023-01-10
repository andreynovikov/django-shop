import { useQuery, useMutation, useQueryClient } from 'react-query';

import { comparisonKeys, loadComparisons, addToComparison, removeFromComparison } from '@/lib/queries';

export default function useComparison(options) {
    const queryClient = useQueryClient();

    const { kind } = options || { kind: null }; // we use null instead of undefined to comply with SSR props in '/compare'

    const { data: comparisons, isSuccess, isLoading, isError } = useQuery(
        comparisonKeys.list(kind),
        () => loadComparisons(kind),
        {
            initialData: [],
            onError: (error) => {
                console.log(error);
            }
        }
    );

    const addToComparisonMutation = useMutation((productId) => addToComparison(productId), {
        onSuccess: (data) => {
            queryClient.setQueryData(comparisonKeys.list(null), data);
        }
    });
    const removeFromComparisonMutation = useMutation((productId) => removeFromComparison(productId), {
        onSuccess: (data) => {
            queryClient.invalidateQueries(comparisonKeys.lists());
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
