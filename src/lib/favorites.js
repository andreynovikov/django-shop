import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { useSession } from '@/lib/session';
import { favoriteKeys, loadFavorites, addToFavorites, removeFromFavorites } from '@/lib/queries';

export default function useFavorites() {
    const { status } = useSession();

    const queryClient = useQueryClient();

    const { data: favorites, isSuccess, isLoading, isError } = useQuery({
        queryKey: favoriteKeys.details(),
        queryFn: () => loadFavorites(),
        enabled: status === 'authenticated',
        initialData: [],
    });

    const addToFavoritesMutation = useMutation({
        mutationFn: (productId) => addToFavorites(productId),
        onSuccess: () => {
            queryClient.invalidateQueries({queryKey: favoriteKeys.all});
        }
    });
    const removeFromFavoritesMutation = useMutation({
        mutationFn: (productId) => removeFromFavorites(productId),
        onSuccess: () => {
            queryClient.invalidateQueries({queryKey: favoriteKeys.all});
        }
    });

    const favoritize = (productId) => {
        addToFavoritesMutation.mutate(productId);
    };

    const unfavoritize = (productId) => {
        removeFromFavoritesMutation.mutate(productId);
    };

    return { favorites, favoritize, unfavoritize, isSuccess, isLoading, isError };
}
